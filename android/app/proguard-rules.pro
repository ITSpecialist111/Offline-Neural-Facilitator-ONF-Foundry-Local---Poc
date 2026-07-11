# LiteRT-LM JNI entry points are discovered from the Kotlin API.
-keep class com.google.ai.edge.litertlm.** { *; }
-keepclasseswithmembernames class * {
    native <methods>;
}
