document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.querySelector('#toggle_btn');
  
    togglePassword.addEventListener('click', function() {
      // Toggle the type attribute
      const password = document.getElementById('id_password');
      const icon = this.querySelector('i');
      
      if (password.type === 'password') {
        password.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        password.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  });