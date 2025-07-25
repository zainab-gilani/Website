from datetime import datetime

from django.utils.html import strip_tags
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import account_activation_token
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from django.contrib import messages


User = get_user_model()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
#endclass

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Deactivate until email is confirmed
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
    return render(request, "accounts/signup.html", { "form": form })
#enddef

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    #endtry

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('coursefinder:coursefinder')
    else:
        return render(request, 'accounts/activation_invalid.html')
    #endif
#enddef

def resend_activation_view(request):
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
        #endif
        return redirect('accounts:resend_activation')
    #endif
    return render(request, 'accounts/resend_activation.html')
#enddef