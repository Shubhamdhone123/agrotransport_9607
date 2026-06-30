
        // Initialize AOS
        AOS.init({
            duration: 1000,
            once: true
        });

        // Preloader


        // Header scroll effect
        window.addEventListener('scroll', () => {
            const header = document.querySelector('.header');
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
