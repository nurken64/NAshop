document.getElementById('signin-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;

    // Send the data to the server for validation
    var xmlreq = new XMLHttpRequest();
    xmlreq.open('POST', 'signin.php', true);
    xmlreq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xmlreq.onreadystatechange = function() {
      if (xmlreq.readyState === XMLHttpRequest.DONE && xmlreq.status === 200) {
        var response = JSON.parse(xmlreq.responseText);
        if (response.success) {
          // User successfully authenticated, redirect to another page or perform other actions
          console.log('User authenticated!');
        } else {
          // Authentication failed, display an error message
          console.log('Authentication failed:', response.message);
        }
      }
    };
    xmlreq.send('email=' + encodeURIComponent(email) + '&password=' + encodeURIComponent(password));
  });
