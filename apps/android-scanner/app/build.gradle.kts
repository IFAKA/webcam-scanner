plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "dev.roomscanner"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.roomscanner"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("com.google.ar:core:1.50.0")
}
