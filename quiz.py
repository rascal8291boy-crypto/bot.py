<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login</title>

<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #111;
}

/* Top Design */
.top {
    height: 30%;
    background: radial-gradient(circle, #1e2a38 20%, #0f1720 100%);
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Logo box */
.logo-box {
    background: white;
    padding: 20px;
    border-radius: 15px;
}

/* Bottom Card */
.card {
    background: #fff;
    height: 65%;
    border-top-left-radius: 40px;
    border-top-right-radius: 40px;
    padding: 30px;
    text-align: center;
    margin-top: 0px;
}

/* Heading */
h2 {
    font-size: 28px;
    margin-bottom: 20px;
}

/* Input Row */
.input-row {
    display: flex;
    margin-bottom: 15px;
}

.country {
    width: 30%;
    background: #eee;
    border-radius: 10px;
    border: none;
    padding: 10px;
}

.phone {
    width: 70%;
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 10px;
}

/* Buttons */
button {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 10px;
    background: #0f1720;
    color: white;
    font-weight: bold;
    margin-top: 10px;
}

.resend {
    background: #007bff;
}

/* Hidden */
.hidden {
    display: none;
}

/* Timer */
#timer {
    color: red;
    font-size: 14px;
}
</style>
</head>

<body>

<div class="top">
    <div class="logo-box">🔷</div>
</div>

<div class="card">

<!-- STEP 1 -->
<div id="step1">
    <h2>Login</h2>

    <div class="input-row">
        <input type="text" id="countryCode" value="+91" class="country">
        <input type="tel" id="phone" placeholder="Mobile Number" class="phone">
    </div>

    <button onclick="sendOTP()">OTP</button>
</div>

<!-- STEP 2 -->
<div id="step2" class="hidden">
    <h2>Enter OTP</h2>

    <p id="timer">OTP expires in: <span id="seconds">60</span>s</p>

    <input type="text" id="otpInput" placeholder="6-digit OTP">

    <button onclick="verifyOTP()">Verify</button>
    <button onclick="resendOTP()" class="resend">Resend OTP</button>
</div>

<!-- STEP 3 -->
<div id="step3" class="hidden">
    <h2>Personal Info</h2>

    <input type="text" id="firstName" placeholder="First Name">
    <input type="text" id="lastName" placeholder="Last Name">

    <button onclick="showWelcome()">Submit</button>
</div>

<!-- STEP 4 -->
<div id="step4" class="hidden">
    <h2 id="welcomeText"></h2>
    <p>Login successful!</p>
</div>

</div>

<script>
let generatedOTP;
let timerInterval;

window.onload = function() {
    if (localStorage.getItem("isLoggedIn") === "true") {
        window.location.href = "dashboard.html";
    }
};

function sendOTP() {
    const phone = document.getElementById('phone').value;

    if (phone.length < 10) return alert("Valid number dalein");

    generatedOTP = Math.floor(100000 + Math.random() * 900000);
    alert("OTP: " + generatedOTP);

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
            alert("OTP expired");
            location.reload();
        }
    }, 1000);
}

function resendOTP() {
    const phone = document.getElementById('phone').value;

    if (phone.length < 10) return alert("Invalid number");

    generatedOTP = Math.floor(100000 + Math.random() * 900000);
    alert("New OTP: " + generatedOTP);

    clearInterval(timerInterval);
    startTimer();
}

function verifyOTP() {
    const enteredOTP = document.getElementById('otpInput').value;

    if (generatedOTP && enteredOTP == generatedOTP) {
        clearInterval(timerInterval);

        document.getElementById('step2').classList.add('hidden');
        document.getElementById('step3').classList.remove('hidden');
    } else {
        alert("Wrong OTP");
    }
}

function showWelcome() {
    const fname = document.getElementById('firstName').value;
    const lname = document.getElementById('lastName').value;

    if (!fname) return alert("Name required");

    localStorage.setItem("isLoggedIn", "true");

    document.getElementById('step3').classList.add('hidden');
    document.getElementById('step4').classList.remove('hidden');

    document.getElementById('welcomeText').innerText = `Welcome ${fname}`;

    setTimeout(() => {
        window.location.href = "dashboard.html";
    }, 3000);
}
</script>

</body>
      </html>
