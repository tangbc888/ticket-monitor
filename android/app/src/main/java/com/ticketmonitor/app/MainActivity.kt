package com.ticketmonitor.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.webkit.*
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.firebase.messaging.FirebaseMessaging

class MainActivity : AppCompatActivity() {
    
    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    
    // 服务器地址，发布时修改为实际部署地址
    private val webUrl = "http://10.0.2.2:3000"  // 模拟器中对应宿主机 localhost
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // 请求通知权限（Android 13+）
        requestNotificationPermission()
        
        // 初始化 WebView
        setupWebView()
        
        // 初始化下拉刷新
        setupSwipeRefresh()
        
        // 获取 FCM Token
        fetchFCMToken()
        
        // 加载网页
        webView.loadUrl(webUrl)
        
        // 处理来自通知点击的 Intent
        handleNotificationIntent()
    }
    
    private fun setupWebView() {
        webView = findViewById(R.id.webView)
        
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true          // 启用 localStorage
            databaseEnabled = true
            allowFileAccess = true
            cacheMode = WebSettings.LOAD_DEFAULT
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            userAgentString = userAgentString + " TicketMonitorApp/1.0"
            
            // 适配移动端
            useWideViewPort = true
            loadWithOverviewMode = true
            setSupportZoom(false)
        }
        
        // 添加 JS Bridge
        webView.addJavascriptInterface(WebAppInterface(this), "AndroidBridge")
        
        // WebViewClient - 所有链接在 WebView 内打开
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false  // 在 WebView 内打开
            }
            
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                swipeRefresh.isRefreshing = false
                
                // 页面加载完成后，通过 JS 传递 FCM token
                injectFCMToken()
            }
        }
        
        // WebChromeClient - 处理 JS 对话框等
        webView.webChromeClient = object : WebChromeClient() {
            override fun onJsAlert(view: WebView?, url: String?, message: String?, result: JsResult?): Boolean {
                return super.onJsAlert(view, url, message, result)
            }
        }
    }
    
    private fun setupSwipeRefresh() {
        swipeRefresh = findViewById(R.id.swipeRefresh)
        swipeRefresh.setColorSchemeColors(
            ContextCompat.getColor(this, R.color.primary)
        )
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }
    }
    
    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) 
                != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                    this, 
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS), 
                    1001
                )
            }
        }
    }
    
    private var fcmToken: String? = null
    
    private fun fetchFCMToken() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                fcmToken = task.result
                // Token 获取成功后注入到 WebView
                injectFCMToken()
            }
        }
    }
    
    private fun injectFCMToken() {
        fcmToken?.let { token ->
            // 通过 JS 将 FCM token 传递给 Web 前端
            webView.evaluateJavascript(
                "if(window.onFCMToken) { window.onFCMToken('$token'); }",
                null
            )
        }
    }
    
    private fun handleNotificationIntent() {
        intent?.getStringExtra("navigate_to")?.let { route ->
            // 从通知点击进来，跳转到对应页面
            webView.loadUrl("$webUrl/$route")
        }
    }
    
    // 返回键处理：优先 WebView 后退，无历史记录时退出应用
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
