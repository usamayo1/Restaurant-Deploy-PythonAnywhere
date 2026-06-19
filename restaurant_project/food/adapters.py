from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile


class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        data = sociallogin.account.extra_data

        # Save Google email
        user.email = data.get("email", user.email)

        # Save first name
        user.first_name = data.get("given_name", user.first_name)

        # Save last name
        user.last_name = data.get("family_name", user.last_name)

        user.save()

        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Save profile picture
        picture_url = data.get("picture")
        if picture_url:
            profile.profile_image = picture_url

        profile.save()

        return user
