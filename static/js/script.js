let invalid_emails = [".ru",".by"]

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

function activate_error(error_name){
    let x = document.getElementById(`for-${error_name}`);
    x.classList.add('form-input__active');
}

function email_validation(email) {
    let validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

    if (email.match(validRegex)) {
        return true;
    } else {
        return false;
    }
}

function checkError(text) {
    let name = text.getAttribute('id');
    let x = document.getElementById(`for-${name}`);
    if(text.value.trim() === ""){
      // let x = `for-${name}`;
      x.classList.add('form-input__active');
    }
    else{
      x.classList.remove('form-input__active');
    }
    // alert(x)
  }
  
  function checkErrors() {
    let inputs = document.querySelectorAll('.form-input');
    for(let element of inputs){
      if(element.value.trim() === ""){
        let name = element.getAttribute('id');
        activate_error(name);
        // alert(element.getAttribute('id'));
      }
    }
  }

  function openPopupForCode(){
    Swal.fire({
        icon:"success",
        title: "Супер!",
        html: "Код відправляється вам на пошту, зачекайте секунду. Якщо лист не прийшов, перегляньте папку 'Спам'",
        timer: 2000,
        showConfirmButton: false,
    })
  }

window.addEventListener("load", (event) => {
    if (window.location.pathname == "/auth/") {
        let login_btn = document.getElementById("login__btn");

        login_btn.addEventListener("click", function (event) {
            event.preventDefault();

            let email = document.getElementById("login__email").value;

            validation = email_validation(email);

            let is_invalid_email = false

            if (invalid_emails.some(ending=>email.endsWith(ending))){
                validation = false
                is_invalid_email = true
            }

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
                    if (response.data["page"] == "check"){
                        openPopupForCode();

                        axios.post("/send_code/",data,
                            {
                                headers: {
                                    'Content-Type': 'application/json',
                                    "X-CSRFToken": csrf_token,
                                }
                            },).then((new_response) => {
                                document.getElementById("body").innerHTML = response.data["html"];

                                document.getElementById("check__log").addEventListener("click", sendCodeData);
                                document.getElementById("check__sendcode").addEventListener("click", sendCodeAgain);
                            })
                    }else{
                        document.getElementById("body").innerHTML = response.data["html"];

                        document.getElementById("register__email").value = email;
            
                        document.getElementById("register__btn").addEventListener("click", sendRegistrationData);
                    }


                }).catch((error) => {
                    console.log(error);
                    activate_error(error.response.data.message);
                })
            }else{
                let error = 'login__email'

                if (is_invalid_email){
                    error = 'ru__email'
                }

                activate_error(error);
            }
        })

        function sendRegistrationData(event) {
            event.preventDefault();

            checkErrors();

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

                openPopupForCode();
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

                    
                    for (let key in error_field){
                        if (key == "first_name"){
                            activate_error("register__fname");
                        }else if (key == "last_name") {
                            activate_error("register__lname");
                        }else{
                            activate_error("register__nickname");
                        }
                    }

                })
            }
        }

        function sendCodeData(event) {
            event.preventDefault();

            checkErrors();

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
                console.log(error)
                activate_error("check__code")
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
        
        function add_last_message(chat_id, message, fullname, photo){

            let chat = document.getElementById(`chat__${chat_id}`);

            if (!chat){
                let chat_list = document.getElementById("chat__list");

                let chatsItem = document.createElement('li');
                chatsItem.classList += "chats__item";
                
                chatsItem.innerHTML = `
                <a id="chat__${chat_id}" href="/${chat_id}" class="chats__link">
                    <img src="${photo}" alt="user photo" class="chats__user-img">
                    <div class="chats__text">
                        <p class="chats__user-name user-name">${fullname}</p>
                        <p class="chats__user-message">Немає повідомлення</p>
                    </div>
                    <div class="chats__notification notification-active"></div>
                </a>
                `

                    chat_list.prepend(chatsItem);

                    chat = document.getElementById(`chat__${chat_id}`);
            }

            chat.getElementsByClassName("chats__user-message")[0].innerText  = message;  

            let chatItem = chat.closest('.chats__item');
            let chatList = chatItem.parentNode;
            
            chatList.prepend(chatItem);
        }

        const sk = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/chat/'
        )
        
        if (window.location.pathname != "/"){
            let chat = document.querySelector(".correspondence__message");

            chat.scrollTo(0, chat.scrollHeight);

            let send_button = document.getElementById("chat__sendbutton");

            send_button.addEventListener("click" , (event) => {
                event.preventDefault();

                let message = document.getElementById('chat__message').value;
                document.getElementById('chat__message').value = "";
                
                if ( 1 > message.length > 512  || message.trim() == ""){
                    return
                }

                
                let chat_id = window.location.pathname.slice(1,-1);

                let data = {
                    "chat_id": chat_id,
                    "message": message,
                }

                sk.send(JSON.stringify(data));

                let no_messages_p = document.getElementById("chat__nomessages");
                if(no_messages_p){
                    no_messages_p.remove();
                }
                
                document.getElementById("new__messages").innerHTML += `<p class="messages__curent-user user-massage">${message}</p>`
                
                add_last_message(chat_id, message);

                message = "";

                let chat = document.querySelector(".correspondence__message");

                chat.scrollTo(0, chat.scrollHeight);
            })
        }

        sk.onmessage = function(event) {

            const message = JSON.parse(event.data);
            console.log(window.location.pathname == `/${message.chat_id}/`)
            if (window.location.pathname == `/${message.chat_id}/`){
                document.getElementById("new__messages").innerHTML += `<p class="messages__other-user user-massage">${message.message}</p>`
                
                let no_messages_p = document.getElementById("chat__nomessages");
                
                if(no_messages_p){
                    no_messages_p.remove();
                }

                let chat = document.querySelector(".correspondence__message");

                chat.scrollTo(0, chat.scrollHeight);
            };
            
            add_last_message(message.chat_id, message.message, message.fullname, message.photo);
          };
    }

});

// search

let timer;

const timeout = 500;

const keyupHeandler = () => {
    clearTimeout(timer);

    timer = setTimeout(() => {
        searchPeople(searchInput)
    }, timeout);
} 

const searchButton = document.querySelector('.search');
const searchBox = document.querySelector('.search-people');
const searchInput = document.querySelector('.search-people__input');
const people_list = document.getElementById("search-people-list")
searchButton.addEventListener('click', function () {
    searchBox.classList.toggle('active');
    if(searchBox.classList.contains('active'))
    {   
        searchInput.readOnly = false;
        searchInput.focus();

        searchInput.addEventListener("keyup", keyupHeandler);
    }
    else{
        searchInput.readOnly = true;
        
        searchInput.removeEventListener("keyup", keyupHeandler);
    }
})

const sidebarTop = document.querySelector('.current-user');
document.addEventListener('click', (e) => {
    if(searchBox.classList.contains('active'))
    {
        const withinInput = e.composedPath().includes(sidebarTop);
        if(!withinInput) {
            searchBox.classList.remove('active');
            if(searchInput.classList.contains('active'))
            {
                searchInput.readOnly = false;
            }
            else{
                searchInput.readOnly = true;

                searchInput.removeEventListener("keyup", keyupHeandler);
            }
        }
    }
})

function searchPeople(input){
    let input_text = input.value;
    
    if (input_text == ""){
        people_list.innerHTML = '';

        return;
    }

    let csrf_token = getCookie('csrftoken');
    let data = {
        "search_input": input_text,
    }

    axios.post("/search_users/",
        data,
        {
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": csrf_token,
            }
        },
        ).then((response) => {
            people_list.innerHTML = '';

            response.data.users.forEach(element => {
                let list_item = document.createElement("li");

                list_item.classList += 'search-people__item';

                list_item.innerHTML = `
                    <a id="" href="/create_new_chat/${element.user_id}" class="search-people__link">
                      <img src="/${element.user_photo}" alt="user photo" class="search-people__user-img">
                      <p class="search-people__name">${element.user_name}</p>
                    </a>
                `

                people_list.appendChild(list_item);
            }
        )
        }).catch((error) => {
            console.log(error)
        }) 

}

function makeReaction(paragraph, message_id,user_id, place){
    paragraph.classList.toggle("like-message");
    paragraph.classList.toggle(`like-${place}`);

    data = {
        message: message_id,
        user: user_id,
    }

    let csrf_token = getCookie('csrftoken');

    axios.post(
        "/make_reaction_on_message/",
        data,
        {
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": csrf_token,
            }
        })
}

// popup
let settingBtn = document.querySelector('.setting');
let settingBox = document.querySelector('.settings-box');
settingBtn.addEventListener("click", () => {
    settingBox.classList.toggle('active');
});
