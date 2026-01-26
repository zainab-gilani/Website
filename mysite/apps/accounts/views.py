import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode

from .forms import CustomUserCreationForm
from .models import SavedMatch
from .tokens import account_activation_token

User = get_user_model()


def register_view(request):
    """
    Handles user registration and sends activation email.

    :param request: Django HTTP request object
    :return: Rendered HTML response for signup page or success page
    """
    # Redirect to profile if already logged in
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email is confirmed
            user.save()

            current_site = request.get_host()
            mail_subject = 'Activate your account'
            message = render_to_string('accounts/acc_active_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            message_text = strip_tags(message)

            mail_subject = f"Activate your account (requested {datetime.now().strftime('%d/%m/%Y %H:%M:%S')})"
            to_email = form.cleaned_data.get('email')

            email = EmailMultiAlternatives(
                mail_subject,
                message_text,
                'unimatch.nea@gmail.com',
                [to_email]
            )
            email.attach_alternative(message, "text/html")
            email.send()
            return render(request, 'accounts/signup_success.html', {
                'user_email': user.email
            })

    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


# enddef

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        # Redirect to profile if already logged in
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


# endclass

def activate(request, uidb64, token):
    """
    Activates user account from email verification link.

    :param request: Django HTTP request object
    :param uidb64: Base64 encoded user ID
    :param token: Account activation token
    :return: Redirect to coursefinder page or activation invalid page
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # endtry

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('coursefinder:coursefinder')
    else:
        return render(request, 'accounts/activation_invalid.html')
    # endif


# enddef

def resend_activation_view(request):
    """
    Resends activation email to user if account is inactive.

    :param request: Django HTTP request object
    :return: Rendered HTML response for resend activation page
    """
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user and not user.is_active:
            current_site = request.get_host()
            mail_subject = f"Activate your account (requested {datetime.now().strftime('%d/%m/%Y %H:%M:%S')})"
            message = render_to_string('accounts/acc_active_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            message_text = strip_tags(message)
            email_msg = EmailMultiAlternatives(
                mail_subject,
                message_text,
                'unimatch.nea@gmail.com',
                [email]
            )
            email_msg.attach_alternative(message, "text/html")
            email_msg.send()
            messages.success(request, 'Activation link resent! Check your inbox.')
        else:
            messages.error(request, 'No inactive account found with that email.')
        # endif
        return redirect('accounts:resend_activation')
    # endif
    return render(request, 'accounts/resend_activation.html')


# enddef


@login_required
def profile_view(request):
    """
    Handles user profile page including updates and account deletion.

    :param request: Django HTTP request object
    :return: Rendered HTML response for profile page or redirect
    """
    user = request.user
    error = None

    if request.method == 'POST':
        # DELETE ACCOUNT
        if 'delete_account' in request.POST:
            user.delete()
            return redirect('coursefinder:guest_coursefinder')
        # endif

        # SAVE PROFILE CHANGES
        if 'save_changes' in request.POST:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            new_password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')

            something_changed = False

            # Username update
            if username and username != user.username:
                if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    error = "Username already taken."
                else:
                    user.username = username
                    something_changed = True
                # endif
            # endif

            # Email update
            if not error and email and email != user.email:
                if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                    error = "Email already used."
                else:
                    user.email = email
                    something_changed = True
                # endif
            # endif

            # Password update
            if not error and new_password:
                if new_password != confirm_password:
                    error = "Passwords do not match."
                elif len(new_password) < 8:
                    error = "Password must be at least 8 characters."
                else:
                    user.set_password(new_password)
                    something_changed = True
                # endif

            # Save changes if no error
            if not error and something_changed:
                user.save()
                messages.success(request, "Profile updated successfully!")
                # If password changed, keep user logged in
                if new_password:
                    update_session_auth_hash(request, user)
                # endif
                return redirect('accounts:profile')
            else:
                messages.error(request, error)
            # endif
        # endif
    # endif

    context = {
        "user": user,
    }
    return render(request, 'accounts/profile.html', context)


# enddef

@login_required
def saved_matches_view(request):
    """
    Displays all courses saved by the logged-in user.

    :param request: Django HTTP request object
    :return: Rendered HTML response for saved matches page
    """
    saved_matches = SavedMatch.objects.filter(user=request.user)
    # Add is_saved property to each saved match for template consistency
    for match in saved_matches:
        match.is_saved = True
    # endfor
    return render(request, 'accounts/saved_matches.html', {'results': saved_matches})


# enddef

@login_required
def save_match(request):
    """
    Saves a course match to the user's saved matches list.

    :param request: Django HTTP request object containing course data in JSON body
    :return: JSON response with save status and match ID
    """
    if request.method == 'POST':
        try:
            # Get the course data from the request
            data = json.loads(request.body)

            # Remove extra whitespace from the data to make sure matching works properly
            university = data['university'].strip()
            course = data['course'].strip()
            course_type = data['course_type'].strip()
            duration = data['duration'].strip()
            requirements = data['requirements'].strip()
            course_link = data['course_link'].strip()

            # Save the match to the database (or get it if it already exists)
            saved_match, was_created = SavedMatch.objects.get_or_create(
                user=request.user,
                university=university,
                course=course,
                course_type=course_type,
                duration=duration,
                requirements=requirements,
                course_link=course_link,
            )

            # Send back success response
            return JsonResponse({'status': 'saved', 'id': saved_match.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # endtry

    return JsonResponse({'status': 'error'}, status=400)


# enddef

@login_required
def unsave_match(request):
    """
    Removes a course match from the user's saved matches list.

    :param request: Django HTTP request object containing course data in JSON body
    :return: JSON response with unsave status and deletion count
    """
    if request.method == 'POST':
        try:
            # Get the course data from the request
            data = json.loads(request.body)

            # Remove extra whitespace from the data
            university = data['university'].strip()
            course = data['course'].strip()
            course_link = data['course_link'].strip()

            # Find all saved matches with these details and delete them
            # We only check university, course, and link to make sure it matches properly
            matches_to_delete = SavedMatch.objects.filter(
                user=request.user,
                university=university,
                course=course,
                course_link=course_link,
            )

            # Count how many we're deleting
            count = matches_to_delete.count()

            # Delete them
            matches_to_delete.delete()

            # Check if we actually deleted anything
            if count > 0:
                return JsonResponse({'status': 'unsaved', 'deleted': count})
            else:
                return JsonResponse({'status': 'not_found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # endtry

    return JsonResponse({'status': 'error'}, status=400)


# enddef


@login_required
def check_saved(request):
    """
    Checks if a course is in the user's saved matches list.

    :param request: Django HTTP request object containing course data in JSON body
    :return: JSON response with is_saved boolean
    """
    if request.method == 'POST':
        try:
            # Get the course data from the request
            data = json.loads(request.body)

            # Remove extra whitespace
            university = data['university'].strip()
            course = data['course'].strip()
            course_link = data['course_link'].strip()

            # Check if this course is in the user's saved matches
            # We only check university, course, and link
            is_saved = SavedMatch.objects.filter(
                user=request.user,
                university=university,
                course=course,
                course_link=course_link,
            ).exists()

            # Send back whether it's saved or not
            return JsonResponse({'is_saved': is_saved})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # endtry

    return JsonResponse({'status': 'error'}, status=400)
# enddef
