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
        versionCode = 7
        versionName = "1.6"
    }

    // مفتاح توقيع ثابت داخل المشروع: كل نسخة يبنيها GitHub تُوقَّع بنفس المفتاح فتتثبّت فوق السابقة
    // (للاستخدام الشخصي فقط. للنشر على Google Play استخدم مفتاحًا سريًا خاصًا بك).
    signingConfigs {
        create("shared") {
            storeFile = file("shared.keystore")
            storePassword = "android"
            keyAlias = "schedule"
            keyPassword = "android"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("shared")
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("shared")
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
