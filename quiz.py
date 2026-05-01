<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Login</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f9; margin: 0; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #218838; }
        .hidden { display: none; }
        #timer { color: red; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>

<div class="card">
    <!-- Step 1: Mobile Number -->
    <div id="step1">
        <h2>Login</h2>
        <div style="display: flex;">
            <input type="text" id="countryCode" value="+91" style="width: 25%; margin-right: 5%;">
            <input type="tel" id="phone" placeholder="Mobile Number" style="width: 70%;">
        </div>
        <button onclick="sendOTP()">Send OTP</button>
    </div>

    <!-- Step 2: OTP Entry -->
    <div id="step2" class="hidden">
        <h2>Enter OTP</h2>
        <p id="timer">OTP expires in: <span id="seconds">60</span>s</p>
        <input type="text" id="otpInput" maxlength="6" placeholder="6-digit OTP">
        <button onclick="verifyOTP()">Verify OTP</button>
    </div>

    <!-- Step 3: Name Entry -->
    <div id="step3" class="hidden">
        <h2>Personal Info</h2>
        <input type="text" id="firstName" placeholder="First Name">
        <input type="text" id="lastName" placeholder="Last Name">
        <button onclick="showWelcome()">Submit</button>
    </div>

    <!-- Final: Welcome Message & Redirection -->
    <div id="step4" class="hidden">
        <h1 id="welcomeText"></h1>
        <p>Aapka login safal raha!</p>
        <p style="color: gray; font-size: 12px;">Redirecting to Dashboard...</p>
    </div>
</div>

<script>
    let generatedOTP;
    let timerInterval;

    // --- NEW: AUTO-LOGIN CHECK (App khulte hi check karega) ---
    window.onload = function() {
        if (localStorage.getItem("isLoggedIn") === "true") {
            // Agar pehle se login hai, toh seedha dashboard par bhej do
            window.location.href = "dashboard.html"; 
        }
    };

    function sendOTP() {
        const phone = document.getElementById('phone').value;
        if (phone.length < 10) return alert("Valid number dalein");

        generatedOTP = Math.floor(100000 + Math.random() * 900000);
        alert("Aapka OTP hai: " + generatedOTP); 

        document.getElementById('step1').classList.add('hidden');
        document.getElementById('step2').classList.remove('hidden');
        startTimer();
    }

    function startTimer() {
        let timeLeft = 60;
        timerInterval = setInterval(() => {
            timeLeft--;
            document.getElementById('seconds').innerText = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                generatedOTP = null;
                alert("OTP expire ho gaya. Refresh karein.");
                location.reload();
            }
        }, 1000);
    }

    function verifyOTP() {
        const enteredOTP = document.getElementById('otpInput').value;
        if (generatedOTP && enteredOTP == generatedOTP) {
            clearInterval(timerInterval);
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('step3').classList.remove('hidden');
        } else {
            alert("Galat ya expired OTP!");
        }
    }

    function showWelcome() {
        const fname = document.getElementById('firstName').value;
        const lname = document.getElementById('lastName').value;
        const phoneNum = document.getElementById('phone').value;

        if (!fname) return alert("Naam bharna zaroori hai");

        // --- NEW: SUCCESS HONE PAR DATA SAVE KAREIN ---
        localStorage.setItem("isLoggedIn", "true");
        localStorage.setItem("userFirstName", fname);
        localStorage.setItem("userLastName", lname);
        localStorage.setItem("userPhone", phoneNum);

        document.getElementById('step3').classList.add('hidden');
        document.getElementById('step4').classList.remove('hidden');
        document.getElementById('welcomeText').innerText = `Welcome, ${fname} ${lname}!`;

        setTimeout(() => {
            window.location.href = "dashboard.html"; 
        }, 3000);
    }
</script>

</body>
</html>
