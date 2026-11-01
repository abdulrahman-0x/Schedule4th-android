plugins {
    id("com.android.application")
}

android {
    namespace = "com.example.schedule4th"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.example.schedule4th"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // للاستخدام الشخصي: توقيع نسخة release بمفتاح debug لتكون قابلة للتثبيت مباشرة.
            // للنشر على Google Play استبدلها بمفتاح توقيع خاص بك.
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.webkit:webkit:1.12.1")
}
