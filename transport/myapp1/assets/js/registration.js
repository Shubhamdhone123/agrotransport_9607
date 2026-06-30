
        document.getElementById('registerForm').addEventListener('submit', function(e) {
            e.preventDefault();
            // Add your form validation and submission logic here
            console.log('Form submitted');
        });

        document.addEventListener('DOMContentLoaded', function() {
            const video = document.querySelector('video');

            // Handle video loading error
            video.addEventListener('error', function(e) {
                console.log('Video loading error:', e);
                document.body.style.backgroundImage = "linear-gradient(rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.9)), url('https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?ixlib=rb-4.0.3')";
                document.body.style.backgroundSize = "cover";
                document.body.style.backgroundPosition = "center";
                document.body.style.backgroundAttachment = "fixed";
            });

            // Log when video starts playing
            video.addEventListener('playing', function() {
                console.log('Video is playing');
            });
        });
