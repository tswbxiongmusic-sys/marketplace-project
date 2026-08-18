# ຕັ້ງຄ່າ Login ຜ່ານ Google ແລະ Facebook

ລະບົບໃຊ້ OAuth ຂອງ `django-allauth`: ລູກຄ້າຢືນຢັນກັບ Google ຫຼື Facebook ໂດຍກົງ ແລະ ເວັບບໍ່ເຫັນ ຫຼື ບໍ່ເກັບລະຫັດຜ່ານຂອງບັນຊີນັ້ນ.

## 1. ກຳນົດ URL ຂອງເວັບ

ກ່ອນຕັ້ງຄ່າໃຫ້ຈົດ URL ຂອງທ່ານ. ຕົວຢ່າງໃນເຄື່ອງ:

```text
http://127.0.0.1:8000
```

ແລະ ຫຼັງຈາກນຳຂຶ້ນອອນລາຍ:

```text
https://marketplace.example.com
```

ລະບົບນີ້ໃຊ້ callback ຢູ່ພາຍໃຕ້ `/social/` ເສມີ.

## 2. Google OAuth

1. ເຂົ້າ Google Cloud Console, ສ້າງ project ແລະຕັ້ງ OAuth consent screen.
2. ສ້າງ Credentials ປະເພດ **OAuth client ID → Web application**.
3. ໃນ **Authorized redirect URIs**, ເພີ່ມ URL ໃຫ້ກົງຕົວອັກສອນ:

   ```text
   http://127.0.0.1:8000/social/google/login/callback/
   https://YOUR-DOMAIN/social/google/login/callback/
   ```

4. ເພີ່ມ Authorized JavaScript origin ຕາມ domain ຂອງທ່ານ, ເຊັ່ນ `https://YOUR-DOMAIN`.
5. ບັນທຶກ **Client ID** ແລະ **Client secret** ເພື່ອໃສ່ເປັນ environment variables. ຫ້າມສົ່ງ Client secret ໃຫ້ຜູ້ອື່ນ.

## 3. Facebook Login

1. ເຂົ້າ Meta for Developers, ສ້າງ App ປະເພດທີ່ຮອງຮັບ Facebook Login ແລະ ເພີ່ມ product **Facebook Login**.
2. ໃນ Facebook Login settings, ໃສ່ **Valid OAuth Redirect URIs** ໃຫ້ກົງຕົວອັກສອນ:

   ```text
   http://127.0.0.1:8000/social/facebook/login/callback/
   https://YOUR-DOMAIN/social/facebook/login/callback/
   ```

3. ໃສ່ App Domains ແລະ Site URL ເປັນ domain ຂອງຮ້ານ. ເມື່ອຈະໃຫ້ລູກຄ້າທົ່ວໄປໃຊ້ ໃຫ້ເຮັດໃຫ້ app ຢູ່ໃນ Live mode ແລະ ປະຕິບັດຕາມຂໍ້ກຳນົດ Meta.
4. ບັນທຶກ **App ID** ແລະ **App Secret**. ຫ້າມນຳ App Secret ໄປໃສ່ frontend ຫຼື commit ລົງ Git.

## 4. ໃສ່ຄ່າໃນເຄື່ອງ ຫຼື ໃນ hosting

ສຳລັບ local ໃຫ້ສ້າງ `.env` ຈາກ `.env.example`. ສຳລັບ server ໃຫ້ໃສ່ໃນ Secret Environment Variables ຂອງ hosting:

```dotenv
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
```

ໃສ່ຄົບທັງ ID ແລະ secret ແລ້ວ restart/deploy ໃໝ່. ຖ້າປ່ອຍຄ່າໃດຄ່າໜຶ່ງວ່າງ, ປຸ່ມຂອງ provider ນັ້ນຈະບໍ່ສະແດງ.

> ຢ່າສ້າງ Google/Facebook SocialApp ຊ້ຳໃນ Django admin: ໂຄງການນີ້ເລືອກຕັ້ງຄ່າຈາກ environment variables ເທົ່ານັ້ນ ເພື່ອໃຫ້ secret ບໍ່ເຂົ້າຖານຂໍ້ມູນ. SocialApp ເກົ່າໃນ admin ຈະຖືກຂ້າມເມື່ອມີຄ່າ environment ຄົບ; ຢ່າລຶບມັນຈົນກວ່າຈະທົດສອບ login ສຳເລັດ.

## 5. ທົດສອບ

1. ຮັນ migration ແລະເປີດ server: `python manage.py migrate` ແລ້ວ `python manage.py runserver`.
2. ເປີດຫນ້າ `/accounts/login/` ໃນປ່ອງ incognito.
3. ກົດ Google ຫຼື Facebook, ເລືອກບັນຊີ, ແລ້ວກວດວ່າກັບມາໜ້າຫຼັກໃນສະຖານະ logged in.
4. ລອງຍົກເລີກທີ່ provider ແລະ ກວດວ່າໜ້າ error ພາສາລາວສະແດງຢ່າງປອດໄພ.

ກ່ອນນຳຂຶ້ນ production, ເຂົ້າ Django admin → **Sites** ແລະ ປ່ຽນ site ID ທີ່ໃຊ້ (`SITE_ID=1` ຕາມຄ່າປັດຈຸບັນ) ໃຫ້ເປັນ domain ຈິງຂອງຮ້ານ. ບໍ່ຕ້ອງສ້າງ SocialApp ໃນ admin.

ບັນຊີ social ໃໝ່ທີ່ສະໝັກຜ່ານ OAuth ບໍ່ມີລະຫັດຜ່ານ Django ທີ່ຕັ້ງໄວ້. ເພື່ອຄວາມປອດໄພ, ລະບົບບໍ່ນຳ social account ໄປລວມກັບ password account ທີ່ມີອີເມວຄືກັນໂດຍອັດຕະໂນມັດ.
