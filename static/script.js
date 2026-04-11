const BASE_URL = ""; // keep empty for Render

document.addEventListener("DOMContentLoaded", function () {

    let currentUser = localStorage.getItem("user");

    // ================= LOGIN PAGE =================

    if (document.getElementById("loginBox")) {

        window.showRegister = function () {
            document.getElementById("loginBox").classList.add("hidden");
            document.getElementById("registerBox").classList.remove("hidden");
        };

        window.showLogin = function () {
            document.getElementById("registerBox").classList.add("hidden");
            document.getElementById("loginBox").classList.remove("hidden");
        };

        window.togglePassword = function (id) {
            let input = document.getElementById(id);
            input.type = input.type === "password" ? "text" : "password";
        };

        function validate(username, password, userErr, passErr) {
            let valid = true;

            document.getElementById(userErr).innerText = "";
            document.getElementById(passErr).innerText = "";

            if (!username) {
                document.getElementById(userErr).innerText = "Username required";
                valid = false;
            }

            if (!password) {
                document.getElementById(passErr).innerText = "Password required";
                valid = false;
            } else if (password.length < 4) {
                document.getElementById(passErr).innerText = "Minimum 4 characters required";
                valid = false;
            }

            return valid;
        }

        window.register = function () {
            let username = document.getElementById("reg_user").value;
            let password = document.getElementById("reg_pass").value;

            if (!validate(username, password, "reg_user_error", "reg_pass_error")) return;

            fetch("/register", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username, password})
            })
            .then(res => res.json())
            .then(() => {
                alert("Registered successfully!");
                showLogin();
            })
            .catch(() => alert("Registration failed"));
        };

        window.login = function () {
            let username = document.getElementById("login_user").value;
            let password = document.getElementById("login_pass").value;

            if (!validate(username, password, "login_user_error", "login_pass_error")) return;

            fetch("/login", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username, password})
            })
            .then(res => {
                if (!res.ok) throw new Error();
                return res.json();
            })
            .then(data => {
                localStorage.setItem("user", data.username);
                window.location.href = "/dashboard";
            })
            .catch(() => {
                document.getElementById("login_pass_error").innerText =
                    "Invalid username or password";
            });
        };
    }

    // ================= DASHBOARD PAGE =================

    if (document.getElementById("dashboard")) {

        if (!currentUser) {
            alert("Please login first");
            window.location.href = "/";
            return;
        }

        document.getElementById("welcomeUser").innerText =
            "👋 Welcome, " + currentUser;

        window.logout = function () {
            localStorage.removeItem("user");
            window.location.href = "/";
        };

        window.addAppliance = function () {

            let name = document.getElementById("a_name").value;
            let power = document.getElementById("a_power").value;
            let hours = document.getElementById("a_hours").value;

            if (!name || !power || !hours) {
                alert("Fill all fields");
                return;
            }

            fetch("/appliance/add/" + currentUser, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    name: name,
                    power: parseFloat(power),
                    hours_per_day: parseFloat(hours)
                })
            })
            .then(res => res.json())
            .then(() => {
                alert("Appliance Added!");

                // Clear fields
                document.getElementById("a_name").value = "";
                document.getElementById("a_power").value = "";
                document.getElementById("a_hours").value = "";

                loadDashboard();
            })
            .catch(() => alert("Error adding appliance"));
        };

        let barChart, pieChart;

        function loadDashboard() {

            // 🔥 Loading effect
            document.body.style.opacity = "0.6";

            fetch("/appliance/all/" + currentUser)
            .then(res => res.json())
            .then(data => {
                let names = data.map(a => a.name);
                let energy = data.map(a => a.daily_energy || 0);

                drawBarChart(names, energy);
                drawPieChart(names, energy);
            });

            fetch("/energy/daily/" + currentUser)
            .then(res => res.json())
            .then(data => {
                document.getElementById("dailyEnergy").innerText =
                    data.daily_energy_kwh;
            });

            fetch("/recommend/" + currentUser)
            .then(res => res.json())
            .then(data => {

                document.getElementById("bill").innerText =
                    "₹ " + data.monthly_bill_estimate;

                // Better styled tips
                document.getElementById("tips").innerHTML =
                    data.tips.map(t => `<li>${t}</li>`).join("");

                document.body.style.opacity = "1"; // done loading
            });
        }

        function drawBarChart(labels, data) {
            if (barChart) barChart.destroy();

            barChart = new Chart(document.getElementById("barChart"), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Energy (kWh)',
                        data: data
                    }]
                }
            });
        }

        function drawPieChart(labels, data) {
            if (pieChart) pieChart.destroy();

            pieChart = new Chart(document.getElementById("pieChart"), {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data
                    }]
                }
            });
        }

        loadDashboard();
    }

});