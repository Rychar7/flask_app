console.clear();

const loginBtn = document.getElementById('login');
const signupBtn = document.getElementById('signup');

loginBtn.addEventListener('click', (e) => {
    let parent = e.target.parentNode.parentNode;
    if (!parent.classList.contains("slide-up")) {
        parent.classList.add('slide-up');
    } else {
        signupBtn.parentNode.parentNode.classList.remove('slide-up');
    }
});

signupBtn.addEventListener('click', (e) => {
    let parent = e.target.parentNode;
    if (!parent.classList.contains("slide-up")) {
        parent.classList.add('slide-up');
    } else {
        loginBtn.parentNode.parentNode.classList.remove('slide-up');
    }
});
