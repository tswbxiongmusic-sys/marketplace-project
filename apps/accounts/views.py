from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import ProfileForm, SellerApplicationForm, SignUpForm

def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
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


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form})


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
