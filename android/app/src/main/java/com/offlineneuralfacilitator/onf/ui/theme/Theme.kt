package com.offlineneuralfacilitator.onf.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Color(0xFFB11F4B),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFFBE8EE),
    onPrimaryContainer = Color(0xFF4B071D),
    secondary = Color(0xFF0078D4),
    tertiary = Color(0xFF16823E),
    background = Color(0xFFF7F4EF),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFF2F0ED),
    onSurface = Color(0xFF242424),
    onSurfaceVariant = Color(0xFF5C5C5C),
    outline = Color(0xFFDEDEDE),
    error = Color(0xFFB42318),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFFD8EA1),
    onPrimary = Color(0xFF3A0717),
    primaryContainer = Color(0xFF6D1633),
    onPrimaryContainer = Color(0xFFFFD9E1),
    secondary = Color(0xFF67B7F7),
    tertiary = Color(0xFF4ADE80),
    background = Color(0xFF343231),
    surface = Color(0xFF292929),
    surfaceVariant = Color(0xFF333333),
    onSurface = Color(0xFFDEDEDE),
    onSurfaceVariant = Color(0xFFB0B0B0),
    outline = Color(0xFF474747),
    error = Color(0xFFFFB4AB),
)

@Composable
fun OnfTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = OnfTypography,
        content = content,
    )
}
