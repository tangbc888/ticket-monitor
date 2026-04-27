package com.ticketmonitor.app

import android.content.Context
import android.webkit.JavascriptInterface
import android.widget.Toast
import com.google.firebase.messaging.FirebaseMessaging

class WebAppInterface(private val context: Context) {
    
    /**
     * 获取 FCM Token - Web 端可调用此方法获取设备的推送 token
     * JS 调用方式: AndroidBridge.getFCMToken()
     */
    @JavascriptInterface
    fun getFCMToken(): String {
        return context.getSharedPreferences("fcm", Context.MODE_PRIVATE)
            .getString("fcm_token", "") ?: ""
    }
    
    /**
     * 显示 Android 原生 Toast 提示
     * JS 调用方式: AndroidBridge.showToast("消息内容")
     */
    @JavascriptInterface
    fun showToast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
    
    /**
     * 获取设备信息
     * JS 调用方式: AndroidBridge.getDeviceInfo()
     */
    @JavascriptInterface
    fun getDeviceInfo(): String {
        return """{"platform":"android","version":"${android.os.Build.VERSION.SDK_INT}","model":"${android.os.Build.MODEL}"}"""
    }
    
    /**
     * 检查是否在 App 内运行
     * JS 调用方式: AndroidBridge.isInApp()
     */
    @JavascriptInterface
    fun isInApp(): Boolean {
        return true
    }
}
