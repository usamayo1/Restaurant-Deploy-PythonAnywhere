from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile


class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        data = sociallogin.account.extra_data

        # Save user information if available
        if data.get("email"):
            user.email = data["email"]

        if data.get("given_name"):
            user.first_name = data["given_name"]

        if data.get("family_name"):
            user.last_name = data["family_name"]

        user.save()

        # Create or update profile
        profile, created = UserProfile.objects.get_or_create(user=user)

        if data.get("picture"):
            profile.profile_image = data["picture"]

        profile.save()

        return user
