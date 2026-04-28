# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

# class MySocialAccountAdapter(DefaultSocialAccountAdapter):

#     def save_user(self, request, sociallogin, form=None):
#         user = super().save_user(request, sociallogin, form)

#         picture_url = sociallogin.account.extra_data.get('picture')

#         if picture_url:
#             user.userprofile.profile_image = picture_url
#             user.userprofile.save()

#         return user
    
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        picture_url = sociallogin.account.extra_data.get("picture")

        profile, created = UserProfile.objects.get_or_create(user=user)

        if picture_url:
            profile.profile_image = picture_url
            profile.save()

        return user
