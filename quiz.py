<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; overflow-x: hidden; }
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .menu-btn { font-size: 24px; cursor: pointer; }
        .sidebar { position: fixed; left: -260px; top: 0; height: 100%; width: 260px; background: #333; color: white; transition: 0.3s; z-index: 1000; }
        .sidebar.active { left: 0; }
        .profile-section { padding: 30px 20px; text-align: center; background: #222; border-bottom: 1px solid #444; }
        .profile-img-container img { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid #007bff; }
        .side-links a { padding: 15px 25px; display: block; color: white; text-decoration: none; border-bottom: 1px solid #333; cursor: pointer; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; }
        .overlay.active { display: block; }
        
        /* Content Area jahan naye pages load honge */
        #main-content { padding: 20px; min-height: 80vh; }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div id="sidebar" class="sidebar">
        <div class="profile-section">
            <div class="profile-img-container">
                <img src="https://placeholder.com" id="profileDisplay">
            </div>
            <h3 id="sideName">Guest</h3>
            <p id="sideUsername">@username</p>
        </div>
        <nav class="side-links">
            <!-- Yahan link ki jagah hum function call karenge -->
            <a onclick="loadFeature('home.html')"><i class="fas fa-home"></i> &nbsp; Home</a>
            <a onclick="loadFeature('settings.html')"><i class="fas fa-cog"></i> &nbsp; Settings</a>
            <a onclick="loadFeature('wallet.html')"><i class="fas fa-wallet"></i> &nbsp; Wallet</a>
            <a onclick="loadFeature('chat.html')"><i class ="fas fa-chat"></i> &nbsp; chat</a>
            <a href="index.html" style="color: #ff4d4d;"><i class="fas fa-sign-out-alt"></i> &nbsp; Logout</a>
        </nav>
    </div>

    <div id="overlay" class="overlay" onclick="toggleMenu()"></div>

    <div class="navbar">
        <div class="menu-btn" onclick="toggleMenu()"><i class="fas fa-bars"></i></div>
        <h2 style="margin:0; font-size: 18px;">MyApp</h2>
        <div class="menu-btn"><i class="fas fa-search"></i></div>
    </div>

    <!-- YAHAN PAGES LOAD HONGE -->
    <div id="main-content">
        <h2>Welcome!</h2>
        <p>Sidebar se koi bhi option select karein.</p>
    </div>

    <script>
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        // MAGIC FUNCTION: Jo alag-alag files ko load karega
        function loadFeature(fileName) {
            fetch(fileName)
                .then(response => {
                    if (!response.ok) throw new Error("File nahi mili");
                    return response.text();
                })
                .then(data => {
                    document.getElementById('main-content').innerHTML = data; // Content badal diya
                    toggleMenu(); // Menu band kar do
                })
                .catch(err => {
                    alert("Error: Pehle " + fileName + " file banaiye!");
                });
        }

        window.onload = function() {
            document.getElementById('sideName').innerText = localStorage.getItem('userFirstName') || "Guest";
            const img = localStorage.getItem('profilePic');
            if(img) document.getElementById('profileDisplay').src = img;
        };
    </script>
</body>
        </html>
        
