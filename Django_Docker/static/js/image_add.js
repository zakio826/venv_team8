// キャンバスとコンテキストを取得
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const preview = document.getElementById("preview"); // プレビューキャンバスの領域

const image = document.getElementById("image");
const movie = document.getElementById("movie");
const movie_get = document.getElementById("id_movie");

const check = document.getElementById("check");
const checked = document.getElementById("checked");
const control = document.getElementById("control");
let set = false;

const submit = document.getElementById("submit");
submit.disabled = true;




// 描画状態を管理するフラグと座標を初期化
let isDrawing = false;
let startX, startY, width, height;

// バウンディングボックスの座標を初期化
let x_min, x_max, y_min, y_max;
let box_li = [0,0,0,0];

movie.autoplay = false;
movie.muted = true;


function auto_set_box() {
    let w = movie.videoWidth / canvas.width;
    let h = movie.videoHeight / canvas.height;

    document.getElementById(`id_box_x_min`).value = box_li[0] * w;
    document.getElementById(`id_box_y_min`).value = box_li[1] * h;
    document.getElementById(`id_box_x_max`).value = box_li[2] * w;
    document.getElementById(`id_box_y_max`).value = box_li[3] * h;
};


function captureFrame() {
    videoElement.currentTime = 0;
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    return canvasElement.toDataURL('image/jpeg');
};


// 動画の最初のフレームをキャンバスに描画する関数
function drawFirstFrame() {
    
    // キャンバスをクリアして画像を再描画
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0);
};

const customBreak = Object.create(breakPoint);

function auto_fit() {
    console.log("tttt");
    if (canvas.width != preview.getBoundingClientRect().width) {
        set = false;

        canvas.width = preview.getBoundingClientRect().width;
        canvas.height = canvas.width * (movie.videoHeight / movie.videoWidth);

        box_li[0] *= canvas.width / image.width;
        box_li[1] *= canvas.height / image.height;
        box_li[2] *= canvas.width / image.width;
        box_li[3] *= canvas.height / image.height;

        image.width = canvas.width;
        image.height = canvas.height;
        
    }
    if (!set) {
        ctx.drawImage(movie, 0, 0, canvas.width, canvas.height);
        image.src = canvas.toDataURL('image/jpeg');

        set = true;
    }
    // ctx.drawImage(image, 0, 0);
    draw_box(true);
};

document.getElementById("load").onclick = () => {
    customBreak.check();
    auto_fit();
};

movie_get.addEventListener('change', function() {
    movie.src = URL.createObjectURL(movie_get.files[0]);
    movie.onloadedmetadata = function() {
        canvas.width = preview.getBoundingClientRect().width;
        canvas.height = canvas.width * (movie.videoHeight / movie.videoWidth);
        canvas.style = "width: 100%; height: auto;";
        checked.style = "margin: 0;";
        control.style = "";
        
        movie.currentTime = 0;
        
        image.width = canvas.width;
        image.height = canvas.height;
        ctx.drawImage(movie, 0, 0, canvas.width, canvas.height);
        image.src = canvas.toDataURL('image/jpeg');
        ctx.drawImage(image, 0, 0);
    };
    // auto_fit();
});




// 選択済みのバウンディングボックスを描画
function draw_box(order) {
    drawFirstFrame(); // 動画の最初のフレームを描画

    ctx.strokeStyle = "blue"; // 青い線で描画
    
    if (order) ctx.lineWidth = 5;
    else ctx.lineWidth = 1;

    ctx.strokeRect(
        box_li[0],
        box_li[1],
        box_li[2] - box_li[0],
        box_li[3] - box_li[1],
    );
};

const main = document.querySelector("main");

let mouseEvent = true;
let main_x, main_y;
let seeked_x, seeked_y;

function mobile_move (touchObject) {

    // 要素の位置を取得
    const rect = canvas.getBoundingClientRect();
    const rect_main = main.getBoundingClientRect();

    // 要素内におけるタッチ位置を計算
    const x = touchObject.pageX - rect.left + rect_main.left;
    const y = touchObject.pageY - rect.top + rect_main.top;

    return [x, y];
};

// スクロールを禁止にする関数
function disableScroll(event) { event.preventDefault(); };

canvas.addEventListener('touchstart', (e) => {
    auto_fit();

    mouseEvent = false;
    isDrawing = true;

    const touchObject = e.touches[0];

    const coordinate = mobile_move(touchObject);

    startX = coordinate[0];
    startY = coordinate[1];

    seeked_x = 0.5;
    seeked_y = 0.5;
    
    canvas.addEventListener('touchmove', disableScroll, { passive: false }); // スクロール禁止
});

function move_end() {
    if (!mouseEvent) {
        canvas.removeEventListener('touchmove', disableScroll, { passive: false }); // スクロール解除
        mouseEvent = true;
    }
    isDrawing = false;

    // 描画した矩形の座標を表示
    x_min = startX;
    x_max = startX + width;
    if (width < 0) {
        x_min += width;
        x_max -= width;
    }

    y_min = startY;
    y_max = startY + height;
    if (height < 0) {
        y_min += height;
        y_max -= height;
    }

    box_li = [
        x_min,
        y_min,
        x_max,
        y_max
    ];
    console.log(box_li);

    auto_set_box();

    check.checked = true;
    check.disabled = false;
    submit.disabled = false;

    draw_box(true);
};

canvas.addEventListener('touchmove', (e) => {
    if (!isDrawing) return;

    const touchObject = e.changedTouches[0];
    const coordinate = mobile_move(touchObject);
    
    width = coordinate[0] - startX;
    height = coordinate[1] - startY;

    draw_box(); // バウンディングボックスの描画

    // 矩形を赤い線で描画
    ctx.strokeStyle = "red";
    ctx.lineWidth = 3;
    ctx.strokeRect(startX, startY, width, height);

    seeked_x = parseFloat((x/canvas_fix.width).toFixed(6));
    seeked_y = parseFloat((y/canvas_fix.height).toFixed(6));

    if (seeked_x <= 0 || seeked_x >= 1 || seeked_y <= 0 || seeked_y >= 1) move_end();
});

canvas.addEventListener('touchend', () => {
    move_end();
});

canvas.addEventListener("touchcancel", () => {
    move_end();
});


// マウスダウンイベントのリスナーを追加
canvas.addEventListener("mousedown", (e) => {
    if (!mouseEvent) return;
    auto_fit();

    isDrawing = true;
    startX = e.clientX - canvas.getBoundingClientRect().left;
    startY = e.clientY - canvas.getBoundingClientRect().top;
});


// マウスムーブイベントのリスナーを追加
canvas.addEventListener("mousemove", (e) => {
    if (!mouseEvent || !isDrawing) return;

    const x = e.clientX - canvas.getBoundingClientRect().left;
    const y = e.clientY - canvas.getBoundingClientRect().top;

    width = x - startX;
    height = y - startY;

    draw_box(false); // バウンディングボックスの描画

    // 矩形を赤い線で描画
    ctx.strokeStyle = "red";
    ctx.lineWidth = 5;
    ctx.strokeRect(startX, startY, width, height);
});


// マウスアップイベントのリスナーを追加
canvas.addEventListener("mouseup", () => {
    move_end();
    // isDrawing = false;
    // if (!mouseEvent) return;

    // // 描画した矩形の座標を表示
    // x_min = startX;
    // x_max = startX + width;
    // if (width < 0) {
    //     x_min += width;
    //     x_max -= width;
    // }

    // y_min = startY;
    // y_max = startY + height;
    // if (height < 0) {
    //     y_min += height;
    //     y_max -= height;
    // }

    // box_li = [
    //     x_min,
    //     y_min,
    //     x_max,
    //     y_max
    // ];
    // console.log(box_li);

    // auto_set_box();

    // check.checked = true;
    // check.disabled = false;
    // submit.disabled = false;

    // draw_box(true);
});

// マウスアウトイベントのリスナーを追加
canvas.addEventListener("mouseout", () => {
    isDrawing = false;
});

// 選択したバウンディングボックスを強調して描画
function out_box() {
    drawFirstFrame(); // 動画の最初のフレームを描画
    for (let i = 0; i < set.length; i++) {
        if (set[i].checked) draw_box(i); // バウンディングボックスの描画
    }
};

// 選択したバウンディングボックスを削除
function del_box() {
    box_li = [0,0,0,0];

    document.getElementById(`id_box_x_min`).value = null;
    document.getElementById(`id_box_y_min`).value = null;
    document.getElementById(`id_box_x_max`).value = null;
    document.getElementById(`id_box_y_max`).value = null;

    check.checked = false;
    check.disabled = true;
    submit.disabled = true;

    drawFirstFrame(); // 動画の最初のフレームを描画
};


window.onresize = () => {
    if (customBreak.check()) auto_fit();
};