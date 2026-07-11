package com.offlineneuralfacilitator.onf.ai

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build

data class FoundryCompanionStatus(
    val installed: Boolean = false,
    val versionName: String? = null,
    val versionCode: Long? = null,
) {
    val summary: String
        get() = if (installed) {
            "Foundry Local Android ${versionName ?: "preview"} companion detected"
        } else {
            "Foundry Local Android companion not installed"
        }
}

data class GalleryStatus(
    val installed: Boolean = false,
    val versionName: String? = null,
) {
    val summary: String
        get() = if (installed) {
            "Google AI Edge Gallery ${versionName ?: "installed"} detected"
        } else {
            "Google AI Edge Gallery not installed"
        }
}

internal object FoundryCompanionDetector {
    const val PACKAGE_NAME = "com.microsoft.foundrylocal.app"

    fun inspect(context: Context): FoundryCompanionStatus = runCatching {
        val info = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.packageManager.getPackageInfo(PACKAGE_NAME, PackageManager.PackageInfoFlags.of(0))
        } else {
            @Suppress("DEPRECATION")
            context.packageManager.getPackageInfo(PACKAGE_NAME, 0)
        }
        FoundryCompanionStatus(
            installed = true,
            versionName = info.versionName,
            versionCode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                info.longVersionCode
            } else {
                @Suppress("DEPRECATION")
                info.versionCode.toLong()
            },
        )
    }.getOrDefault(FoundryCompanionStatus())
}

internal object GalleryDetector {
    private const val PACKAGE_NAME = "com.google.ai.edge.gallery"

    fun inspect(context: Context): GalleryStatus = runCatching {
        val info = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.packageManager.getPackageInfo(PACKAGE_NAME, PackageManager.PackageInfoFlags.of(0))
        } else {
            @Suppress("DEPRECATION")
            context.packageManager.getPackageInfo(PACKAGE_NAME, 0)
        }
        GalleryStatus(installed = true, versionName = info.versionName)
    }.getOrDefault(GalleryStatus())
}
