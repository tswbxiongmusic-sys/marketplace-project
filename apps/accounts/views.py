from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.shortcuts import redirect, render

from allauth.account.models import EmailAddress

from .forms import ProfileForm, SellerApplicationForm, SignUpForm


def _stylize(form, labels=None):
    for name, field in form.fields.items():
        field.widget.attrs["class"] = "form-control"
        if labels and name in labels:
            field.label = labels[name]
    return form

def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Your account has been created.")
        return redirect("home")
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    form.fields["username"].label = "ຊື່ຜູ້ໃຊ້ ຫຼື ອີເມວ"
    form.fields["password"].label = "ລະຫັດຜ່ານ"
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "ຍິນດີຕ້ອນຮັບກັບຄືນ.")
        return redirect(request.POST.get("next") or "home")
    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect("home")


PASSWORD_FORM_LABELS = {
    "old_password": "ລະຫັດຜ່ານປັດຈຸບັນ",
    "new_password1": "ລະຫັດຜ່ານໃໝ່",
    "new_password2": "ຢືນຢັນລະຫັດຜ່ານໃໝ່",
}


@login_required
def profile(request):
    form = ProfileForm(instance=request.user)
    password_form = _stylize(PasswordChangeForm(user=request.user), PASSWORD_FORM_LABELS)

    if request.method == "POST" and request.POST.get("form_name") == "password":
        password_form = _stylize(
            PasswordChangeForm(user=request.user, data=request.POST),
            PASSWORD_FORM_LABELS,
        )
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "ປ່ຽນລະຫັດຜ່ານສຳເລັດແລ້ວ.")
            return redirect("profile")
    elif request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "ບັນທຶກຂໍ້ມູນສຳເລັດແລ້ວ.")
            return redirect("profile")

    email_verified = EmailAddress.objects.filter(
        user=request.user, email=request.user.email, verified=True
    ).exists()

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "password_form": password_form,
            "email_verified": email_verified,
        },
    )


@login_required
def seller_application(request):
    if request.user.role == request.user.Role.SELLER:
        return redirect("seller_dashboard")
    form = SellerApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        from django.utils import timezone
        request.user.seller_requested_at = timezone.now()
        request.user.save(update_fields=["seller_requested_at"])
        messages.success(request, "Your seller application was sent to the administrator.")
        return redirect("profile")
    return render(request, "accounts/seller_application.html", {"form": form})


@login_required
def notifications(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {"notifications": request.user.notifications.all()[:30]})
