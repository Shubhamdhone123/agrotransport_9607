
        let countdown = 120;
        function startTimer() {
            const timerElement = document.getElementById('timer');
            const interval = setInterval(() => {
                const minutes = Math.floor(countdown / 60);
                const seconds = countdown % 60;
                timerElement.textContent = `Time Remaining: ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
                countdown--;

                if (countdown < 0) {
                    clearInterval(interval);
                    timerElement.textContent = "Time Expired!";
                    timerElement.style.backgroundColor = "#e74c3c";
                    timerElement.style.color = "white";
                    setTimeout(() => {
                        window.location.href = "/dashboard";
                    }, 2000);
                }
            }, 1000);
        }

        // Add loading animation
        document.addEventListener('DOMContentLoaded', function() {
            const buttons = document.querySelectorAll('.payment-button button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    this.style.opacity = '0.7';
                    this.innerHTML += '<span class="loading">Processing...</span>';
                });
            });
        });

        document.addEventListener('mousemove', function(e) {
            const circles = document.querySelectorAll('.circles li');
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;

            circles.forEach(circle => {
                const speed = circle.offsetWidth / 100;
                const translateX = (x * 100 * speed);
                const translateY = (y * 100 * speed);
                circle.style.transform = `translate(${translateX}px, ${translateY}px)`;
            });
        });
