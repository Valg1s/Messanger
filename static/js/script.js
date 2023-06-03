function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function email_validation(email) {
    let validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

    if (email.match(validRegex)) {
        return true;
    } else {
        return false;
    }
}

window.addEventListener("load", (event) => {
    if (window.location.pathname == "/auth/") {
        let login_btn = document.getElementById("login__btn");

        login_btn.addEventListener("click", function (event) {
            event.preventDefault();
            let email = document.getElementById("login__email").value;

            validation = email_validation(email);

            if (validation) {

                let expire_time = new Date();

                expire_time.setTime(expire_time.getTime() + (10 * 60 * 1000))

                expires = "; expires=" + expire_time.toUTCString();

                document.cookie = "email" + "=" + email + expires + "; path=/";

                let data = {
                    "email": email
                }

                let csrf_token = getCookie('csrftoken');

                axios.post("/check_user_account/",
                    data,
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            "X-CSRFToken": csrf_token,
                        }
                    },
                ).then((response) => {

                    document.getElementById("body").innerHTML = response.data["html"];

                    if (response.data["page"] == "registration") {
                        document.getElementById("register__email").value = email;

                        document.getElementById("register__btn").addEventListener("click", sendRegistrationData);
                    } else if (response.data["page"] == "check") {
                        document.getElementById("check__log").addEventListener("click", sendCodeData);
                        document.getElementById("check__sendcode").addEventListener("click", sendCodeAgain);
                    }

                }).catch((error) => {
                    alert(error);
                    //add class "active" to error box
                })
            }
        })

        function sendRegistrationData(event) {
            event.preventDefault();

            fname = document.getElementById("register__fname").value;
            lname = document.getElementById("register__lname").value;
            account_name = document.getElementById("register__nickname").value;
            email = document.getElementById("register__email").value;

            if (fname && lname) {
                data = {
                    "first_name": fname,
                    "last_name": lname,
                    "account_name": account_name,
                    "email": email,
                };

                let csrf_token = getCookie('csrftoken');

                axios.post('/register_user/',
                    data,
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            "X-CSRFToken": csrf_token,
                        }
                    }
                ).then((response) => {
                    document.getElementById("body").innerHTML = response.data["html"];

                    document.getElementById("check__log").addEventListener("click", sendCodeData);
                    document.getElementById("check__sendcode").addEventListener("click", sendCodeAgain);
                }).catch((error) => {
                    let error_field = error.response.data;

                    console.log(error_field);
                })
            } else {
                if (!fname) {
                    //add class "active" to error box
                }

                if (!lname) {
                    //add class "active" to error box
                }
            }

        }

        function sendCodeData(event) {
            event.preventDefault();

            let code = document.getElementById("check__code").value;

            data = {
                "code": code,
            }

            let csrf_token = getCookie('csrftoken');

            axios.post("/login_user/",
                data,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        "X-CSRFToken": csrf_token,
                    }
                }
            ).then((response) => {
                window.location.href = '/';
            }).catch((error) => {
                //add class "active" to error box
            })
        }

        function sendCodeAgain(event) {
            event.preventDefault()

            let email = getCookie("email");

            let data = {
                "email": email,
            }

            let csrf_token = getCookie('csrftoken');

            axios.post("/send_code/",
                data,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        "X-CSRFToken": csrf_token,
                    }
                },
            ).then((response) => {
                console.log(response);
            }).catch((error) => {
                console.log(error)
            }) 
        }

    } else {

        const sk = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/chat/'
        )

        sk.onopen = function() {
            console.log('WebSocket connection established.');
            
            const data = {
                chat_id: 1,
                message: "Hello!" 
              };

            sk.send(JSON.stringify(data));
            // Дополнительная логика, выполняемая после успешного установления соединения
          };

        sk.onmessage = function(event) {
            const message = event.data;
            console.log('Received message:', message);
            // Дополнительная логика, выполняемая при получении сообщения от сервера
          };
          
          sk.onclose = function() {
            console.log('WebSocket connection closed.');
            // Дополнительная логика, выполняемая при закрытии соединения
          };
    }

});


