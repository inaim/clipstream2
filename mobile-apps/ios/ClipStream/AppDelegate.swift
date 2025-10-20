import UIKit
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Configure appearance
        configureAppearance()
        
        // Request notification permissions
        requestNotificationPermissions()
        
        // Register for remote notifications
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // MARK: - Appearance Configuration
    
    func configureAppearance() {
        // Set navigation bar appearance
        let appearance = UINavigationBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .black
        appearance.titleTextAttributes = [.foregroundColor: UIColor.white]
        
        UINavigationBar.appearance().standardAppearance = appearance
        UINavigationBar.appearance().scrollEdgeAppearance = appearance
        
        // Set status bar style
        UIApplication.shared.statusBarStyle = .lightContent
    }
    
    // MARK: - Push Notifications
    
    func requestNotificationPermissions() {
        UNUserNotificationCenter.current().delegate = self
        
        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { granted, error in
            if granted {
                print("✅ Notification permission granted")
            } else if let error = error {
                print("❌ Notification permission error: \(error)")
            }
        }
    }
    
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("📱 Device Token: \(token)")
        
        // Send token to your backend
        sendDeviceTokenToServer(token: token)
    }
    
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ Failed to register for remote notifications: \(error)")
    }
    
    // MARK: - UNUserNotificationCenterDelegate
    
    // Handle notification when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        
        // Handle deep link from notification
        if let urlString = userInfo["url"] as? String,
           let url = URL(string: urlString) {
            handleDeepLink(url: url)
        }
        
        completionHandler()
    }
    
    // MARK: - Deep Linking
    
    func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
        handleDeepLink(url: url)
        return true
    }
    
    func handleDeepLink(url: URL) {
        // Parse deep link and navigate in web view
        print("🔗 Deep link: \(url)")
        
        // Post notification to ViewController
        NotificationCenter.default.post(
            name: NSNotification.Name("HandleDeepLink"),
            object: nil,
            userInfo: ["url": url]
        )
    }
    
    // MARK: - Helper Methods
    
    func sendDeviceTokenToServer(token: String) {
        // Send to your backend API
        guard let url = URL(string: "https://clipstream.app/api/v1/devices/register") else {
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "device_token": token,
            "platform": "ios",
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ Failed to send device token: \(error)")
            } else {
                print("✅ Device token sent successfully")
            }
        }.resume()
    }

    // MARK: UISceneSession Lifecycle

    func application(_ application: UIApplication, configurationForConnecting connectingSceneSession: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }

    func application(_ application: UIApplication, didDiscardSceneSessions sceneSessions: Set<UISceneSession>) {
    }
}

