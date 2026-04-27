# Firebase
-keepattributes *Annotation*
-keep class com.google.firebase.** { *; }
# WebAppInterface
-keepclassmembers class com.ticketmonitor.app.WebAppInterface {
    @android.webkit.JavascriptInterface <methods>;
}
