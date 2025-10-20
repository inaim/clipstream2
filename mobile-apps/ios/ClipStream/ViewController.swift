import UIKit
import WebKit

class ViewController: UIViewController, WKNavigationDelegate, WKUIDelegate {
    
    var webView: WKWebView!
    var activityIndicator: UIActivityIndicatorView!
    
    // MARK: - Configuration
    let webAppURL = "https://clipstream.app" // Change to your production URL
    // For development: let webAppURL = "http://localhost:5173"
    
    override func loadView() {
        // Configure WebView
        let webConfiguration = WKWebViewConfiguration()
        webConfiguration.allowsInlineMediaPlayback = true
        webConfiguration.mediaTypesRequiringUserActionForPlayback = []
        
        // Enable camera and microphone
        webConfiguration.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        
        webView = WKWebView(frame: .zero, configuration: webConfiguration)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.scrollView.bounces = true
        webView.allowsBackForwardNavigationGestures = true
        
        // Enable zoom
        webView.scrollView.minimumZoomScale = 1.0
        webView.scrollView.maximumZoomScale = 3.0
        
        view = webView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Setup activity indicator
        setupActivityIndicator()
        
        // Load web app
        loadWebApp()
        
        // Setup pull to refresh
        setupPullToRefresh()
        
        // Handle network reachability
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleNetworkChange),
            name: NSNotification.Name("NetworkStatusChanged"),
            object: nil
        )
    }
    
    // MARK: - Setup Methods
    
    func setupActivityIndicator() {
        activityIndicator = UIActivityIndicatorView(style: .large)
        activityIndicator.center = view.center
        activityIndicator.hidesWhenStopped = true
        activityIndicator.color = .systemBlue
        view.addSubview(activityIndicator)
    }
    
    func setupPullToRefresh() {
        let refreshControl = UIRefreshControl()
        refreshControl.addTarget(self, action: #selector(handleRefresh), for: .valueChanged)
        webView.scrollView.refreshControl = refreshControl
    }
    
    func loadWebApp() {
        guard let url = URL(string: webAppURL) else {
            showError(message: "Invalid URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        
        activityIndicator.startAnimating()
        webView.load(request)
    }
    
    // MARK: - Actions
    
    @objc func handleRefresh() {
        webView.reload()
        webView.scrollView.refreshControl?.endRefreshing()
    }
    
    @objc func handleNetworkChange() {
        // Reload if network becomes available
        loadWebApp()
    }
    
    // MARK: - WKNavigationDelegate
    
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        activityIndicator.stopAnimating()
        
        // Inject JavaScript to enhance mobile experience
        let js = """
        // Disable text selection for better app feel
        document.body.style.webkitUserSelect = 'none';
        document.body.style.webkitTouchCallout = 'none';
        
        // Add viewport meta if not present
        if (!document.querySelector('meta[name="viewport"]')) {
            var meta = document.createElement('meta');
            meta.name = 'viewport';
            meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            document.head.appendChild(meta);
        }
        
        // Notify native app of page events
        window.addEventListener('load', function() {
            window.webkit.messageHandlers.pageLoaded.postMessage('loaded');
        });
        """
        
        webView.evaluateJavaScript(js, completionHandler: nil)
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        activityIndicator.stopAnimating()
        showError(message: "Failed to load: \(error.localizedDescription)")
    }
    
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        activityIndicator.stopAnimating()
        
        // Show offline page or error
        if (error as NSError).code == NSURLErrorNotConnectedToInternet {
            showOfflinePage()
        } else {
            showError(message: "Connection failed: \(error.localizedDescription)")
        }
    }
    
    // MARK: - WKUIDelegate
    
    // Handle JavaScript alerts
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in
            completionHandler()
        })
        present(alert, animated: true)
    }
    
    // Handle JavaScript confirms
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in
            completionHandler(true)
        })
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in
            completionHandler(false)
        })
        present(alert, animated: true)
    }
    
    // Handle file uploads
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        
        let picker = UIImagePickerController()
        picker.delegate = self
        picker.sourceType = .photoLibrary
        picker.mediaTypes = ["public.movie", "public.image"]
        picker.videoQuality = .typeHigh
        
        // Store completion handler
        self.fileUploadCompletionHandler = completionHandler
        
        present(picker, animated: true)
    }
    
    // MARK: - Helper Methods
    
    var fileUploadCompletionHandler: (([URL]?) -> Void)?
    
    func showError(message: String) {
        let alert = UIAlertController(title: "Error", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Retry", style: .default) { _ in
            self.loadWebApp()
        })
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        present(alert, animated: true)
    }
    
    func showOfflinePage() {
        let html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 20px;
                }
                h1 { font-size: 24px; margin-bottom: 10px; }
                p { font-size: 16px; opacity: 0.9; }
                button {
                    margin-top: 20px;
                    padding: 12px 24px;
                    font-size: 16px;
                    background: white;
                    color: #667eea;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <h1>📡 No Internet Connection</h1>
            <p>Please check your connection and try again.</p>
            <button onclick="window.location.reload()">Retry</button>
        </body>
        </html>
        """
        
        webView.loadHTMLString(html, baseURL: nil)
    }
    
    // MARK: - Status Bar
    
    override var preferredStatusBarStyle: UIStatusBarStyle {
        return .lightContent
    }
}

// MARK: - UIImagePickerControllerDelegate

extension ViewController: UIImagePickerControllerDelegate, UINavigationControllerDelegate {
    
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        
        var fileURL: URL?
        
        if let videoURL = info[.mediaURL] as? URL {
            fileURL = videoURL
        } else if let imageURL = info[.imageURL] as? URL {
            fileURL = imageURL
        }
        
        picker.dismiss(animated: true) {
            if let url = fileURL {
                self.fileUploadCompletionHandler?([url])
            } else {
                self.fileUploadCompletionHandler?(nil)
            }
            self.fileUploadCompletionHandler = nil
        }
    }
    
    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
        picker.dismiss(animated: true) {
            self.fileUploadCompletionHandler?(nil)
            self.fileUploadCompletionHandler = nil
        }
    }
}

