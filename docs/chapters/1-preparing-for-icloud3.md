# Preparing for iCloud3

This chapter explains how to:

- Decide what tracking method you want to use.
- Set up iCloud account for the Find-My-Friends tracking method using the iPhone's FindMy App or for the Family Sharing tracking method using the iPhone's Settings App.

### iCloud3 Tracking Methods

The previous chapter described the tracking methods you can use.

- **Find-My-Friends (fmf)** - Uses the people that you are sharing your location with on the FindMy App. This is probably most efficient method to use in regards of how iCloud locates devices and lets you  track people that are not on your Family Sharing List.
- **Family Sharing (famshr)** - The people you want to track are on your Family Sharing list on your iCloud account, along with other Apple devices you don't want to track. Remember, when you use this tracking method, iCloud will locate all of the devices whether you are tracking them or not.

#### Find-My-Friends Tracking Method and the The FindMy app

The Find-my-Friends (FmF) tracking method locates the people you have set up on iPhone's ```FindMy App > People``` screen. When they are added, their iCloud account email address adds the phone to the *Share Location* list and is used on the iCloud3 track_devices parameter. 

The person's email address ties the phone being tracked on the iCloud3 track_devices parameter (*gary_iphone*)  to the person on the Share My Location list (*gary-icloud-acct@email.com*).

1. Open the FindMy App.
2. Select **People**. Then select **+ Share My Location**.
3. This will open the *Share My Location* popup window. Select the person to add to the list using their mobile phone number or their email address.
4. Select **Send** to send a sharing invitation to that person. 
5. Open the email requesting approval and the **Accept the invitation**. 
6. Verify that Location Sharing is on turned on their iPhone.

![findmy screen](../images/findmy_screen.jpg)

> Go to Apple the support web site [here](https://support.apple.com/en-us/HT210400) for more information on the FindMy App and go [here](https://support.apple.com/en-us/HT201493) for more information on setting up and using Find My Friends.

#### Family Sharing Tracking Method and the Settings App

The Family Sharing list is part of your iCloud account and set up on the Settings App.

1. Open the *Settings*.
2. Select  **Your Profile (Apple ID, iCloud, iTunes & App Store)****. 
3. This will open *Your Apple Profile* screen. 
4. Select **Family Sharing** to open the *Family Sharing* screen.
5. Select **Add Family Member** to open the *Invite via iMessage* popup window.
6. Select **Invite via iMessage**. They be added to the Family Sharing List after they accept the invitation. Verify that Location Sharing is turned on on their iPhone.

![family sharing screen](../images/famshr_screen.jpg)

> Go to Apple the support web site [here](https://support.apple.com/en-us/HT201088) for more information on setting up  and using Family Sharing.

### Trouble shooting - iCloud Verification Process works for a short period

Normally, your iCloud account is used for authentication. You go through the verification process discussed above, the people sharing your location with you are located and everything works as expected. Several months later, access to your account expires and you go through the verification process again.

However, there may be times when you go through the verification process, everything looks normal, the people sharing their location with you are located but iCloud asks for another verification several hours or weeks later. It's as if the access authorization to your account expires immediately. 

!> You must use the *Find-my-Friends* tracking method. The *Family Shari [device_tracker.py](..\..\development area - v2.2.1\device_tracker.py) ng* tracking method will now work.

iCloud3 v2.1 solved this problem by creating a second non-2fa account, logging into that account and setting up the FindMy App and then using that account in the username/password configuration parameters. Since this account does not is not a 2fa account, it need to be verified. The following steps explain how to do this and how it will then tie everything together.

#### Create a new non-2fa Account

This must be done on a PC or Mac. Using the iPhone or iPad will not work.

1. Go to https://appleid.apple.com.
2. Click **Create Your Apple Id** at the top of the screen.
3. Fill in the identification information requested.
4. Fill in your name, birthday, non-2fa email you will are creating, password, etc.
5. Fill in the Phone number and go through the account verification process.

!> At some point, the Apple ID Security screen is displayed. This is where you select to not set up 2fa. This is important.

6. Select **Other Options** on the *Apple ID Security* window.
7. Select **Don't Upgrade** on the *Protect your account* window.
8. Select **Continue** on the *Apple ID & Privacy* window.

#### Setting up your new non-2fa Account

Since this is a new iCloud account, you need to add the people that use the devices you want to track in the `Contacts` screen. You only need to enter their name and the email address of their actual iCloud account. 

1. Go to icloud.com. Log into your new non-2fa account. Agree to the Terms & Conditions.
2. Select **Contacts** to go to the iCloud Contacts screen.
3. For each phone you are tracking, Click **plus-sign (+)** at the bottom. Fill in the First name and the real email address. You will use this address on the FindMy App and on the track_devices parameter for this person.
4. Go to an iPhone or iPad and log into your new non-2fa Account in the *Settings App*. It is a lot easier to do this on a device you will not be tracking. If you do this on a phone you are tracking. you will have Sign out of your real iCloud account and sign into the non-2fa account.
5. Follow the procedures in the *Find-My-Friends Tracking Method and the The FindMy app* paragraph above to add the people you want to track in the FindMy App on this non-2fa account.

!> Verify that the Find My app and your iCloud account at *i*cloud.com* can locate the people you are tracking. They should be displayed on the map in the *FindMy app* when signed into the new non-2fa account and the 'Sharing With ...'  message should be displayed in the app when you are signed into the 2fa account. 

!> **If the devices can not be seen in the app, they will not be located by iCloud3.**

Now that you have verified that everything is set up correctly, sign out of the non-2fa account and sign back into your 2fa account. You will only need to sign back into the non-2fa account if you want to track another device.

Use this non-2fa account in the iCloud username/password configuration parameters.




![setup_fmf_icloud3](../images/setup_fmf_icloud3.jpg)

*Overview of how iCloud3 uses the people's contact information to link the iCloud location to the tracked device*

