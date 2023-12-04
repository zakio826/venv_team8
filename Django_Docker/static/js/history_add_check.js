const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const image = document.getElementById("image");
const preview = document.getElementById("preview");

const set = document.getElementsByName("set");
const box_in = document.getElementsByName("box");
const finish = document.getElementById("finish");
const submit = document.getElementById("submit");
const box_list = document.getElementById("box_list");

const check_list = document.getElementById("check_list");
const switch_width = document.getElementById("switch_width");

const data = data_json;

const confirmation = document.getElementById("confirmation");

const check = document.getElementsByName("check");
const checked = document.getElementsByName("checked");

const check_ctrl = document.getElementById("check_ctrl");
const all_check = document.getElementById("all_check");
const all_check_out = document.getElementById("all_check_out");


// キャンバスサイズを初期化
const x_fix = data.outer_edge[2] - data.outer_edge[0];
const y_fix = data.outer_edge[3] - data.outer_edge[1];

canvas.width = x_fix;
canvas.height = y_fix;

let x_fit = canvas.width / x_fix;
let y_fit = canvas.height / y_fix;

// 描画状態を管理するフラグと座標を初期化
let isDrawing = false;
let startX, startY, width, height;
let x_min, x_max, y_min, y_max;

// アイテム名とバウンディングボックスの座標を初期化
let item_name = data.item;
let box_li = data.box;
const model_check = data.model_check;

for (let i = 0; i < set.length; i++) {

    // アイテムの座標がある場所
    if (box_li[i][4] > 0) {

        document.getElementById(`id_form-${i}-result_class`).value = 0;

        if (!model_check) box_li[i][4] = threshold_conf;

        if (box_li[i][4] > threshold_conf) {
            document.getElementById(`id_form-${i}-result_class`).value = 2;
        } else {
            document.getElementById(`id_form-${i}-result_class`).value = 1;
        }

        check[i].disabled = false;
        box_in[i].disabled = false;
        box_in[i].checked = true;

    } else {
        // box_li[i] = [0,0,0,0,0];
        document.getElementById(`id_form-${i}-result_class`).value = 0;
    }
}
console.log(item_name);


// フォームにアイテムの座標を登録
function auto_set_box(i) {
    if (!box_li[i][4]) return;
    let w = x_fix / canvas.width;
    let h = y_fix / canvas.height;
    
    document.getElementById(`id_form-${i}-box_x_min`).value = (box_li[i][0] * w);
    document.getElementById(`id_form-${i}-box_y_min`).value = (box_li[i][1] * h);
    document.getElementById(`id_form-${i}-box_x_max`).value = (box_li[i][2] * w);
    document.getElementById(`id_form-${i}-box_y_max`).value = (box_li[i][3] * h);

    box_in[i].disabled = false;
    box_in[i].checked = true;
};


// アイテムのチェック状況を表示
function set_confirmation() {
    if (isDrawing) return;

    confirmation.innerHTML = null;
    var div = null;
    for (let i = 0; i < set.length; i++) {
        if (checked[i].innerText != "チェック済み") {
            if (confirmation.innerHTML) {
                div.innerHTML += "、";
                confirmation.appendChild(div);
            }
            var tag = document.createElement('span');
            if (box_li[i][4] > threshold_conf) tag.setAttribute('style', 'color: blue;');
            else if (box_li[i][4] > 0) tag.setAttribute('style', 'color: orange;');
            else tag.setAttribute('style', 'color: red;');
            tag.innerText = `${item_name[i]}`;

            div = document.createElement('div');
            div.setAttribute('class', 'd-inline-block');
            div.appendChild(tag);

            confirmation.appendChild(div);
        }
    }
    if (confirmation.innerHTML) {
        confirmation.appendChild(div);
        confirmation.innerHTML = `${confirmation.innerHTML} <span class="d-block d-sm-inline-block mt-2 mt-sm-0">がチェックされていません。</span>`;
    } else {
        div = document.createElement('div');
        div.setAttribute('class', 'text-center');
        div.innerHTML = '<span style="color: rgb(0, 220, 50)">すべてのアイテム</span> <span class="d-inline-block">がチェック済みです。</span>';
        confirmation.appendChild(div);
    }
};


// 選択済みのバウンディングボックスを描画
function draw_box(order=-1) {

    // キャンバスをクリアして画像を再描画
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, image.width, image.height, 0, 0, canvas.width, canvas.height);
    
    for (let i = 0; i < set.length; i++) {

        // 選択されたアイテムを強調して囲む
        if (i == order) ctx.lineWidth = 5;
        else ctx.lineWidth = 1;
        
        if (box_li[i][4] > threshold_conf) ctx.strokeStyle = "blue"; // 青い線で描画
        else if (box_li[i][4] > 0) ctx.strokeStyle = "orange"; // オレンジ色の線で描画
        else ctx.strokeStyle = "red"; // 赤い線で描画

        if (checked[i].innerText == "チェック済み") {
            ctx.strokeStyle = `rgb(0, 220, 50)`; // 緑色の線で描画

            // チェック済みの場合にチェック済みのアイテムのみを強調して囲む
            if (order == -2) ctx.lineWidth = 3;
        }

        // アイテムを指定した線で囲む
        ctx.strokeRect(
            box_li[i][0],
            box_li[i][1],
            box_li[i][2] - box_li[i][0],
            box_li[i][3] - box_li[i][1],
        );
    }
    set_confirmation();
};


const customBreak = Object.create(breakPoint);

// 画面サイズに合わせて要素を最適化
function auto_fit() {
    console.log("true");

    
    console.log(`preview.width:  ${preview.getBoundingClientRect().width} px`);
    console.log(`preview.height: ${preview.getBoundingClientRect().height} px`);
    console.log(`canvas.width:  ${canvas.width} px`);
    console.log(`canvas.height: ${canvas.height} px`);

    x_fit = preview.getBoundingClientRect().width.toFixed() / canvas.width;
    y_fit = preview.getBoundingClientRect().height.toFixed() / canvas.height;

    for (let i = 0; i < set.length; i++) {
        box_li[i][0] *= x_fit;
        box_li[i][1] *= y_fit;
        box_li[i][2] *= x_fit;
        box_li[i][3] *= y_fit;
    }
    
    canvas.width = preview.getBoundingClientRect().width.toFixed();
    canvas.height = canvas.width * (y_fix / x_fix);

    ctx.drawImage(image, 0, 0, image.width, image.height, 0, 0, canvas.width, canvas.height);

    // console.log(`customBreak.last : ${customBreak.last}`);

    if (customBreak.last >= 2) {
        var max_h = canvas.height - check_ctrl.getBoundingClientRect().height - 16;;
        switch_width.style.width = "auto";
        check_list.style.marginTop = "auto";
    } else {
        var max_h = 200;
        switch_width.style.width = 200 * set.length;
        check_list.style.marginTop = "20px";
    }
    check_list.style.height = max_h;

    draw_box();

};


// 画像の読み込みが完了したらキャンバスに描画
image.onload = () => {
    canvas.width = image.width;
    canvas.height = image.height;

    x_fit = canvas.width / x_fix;
    y_fit = canvas.height / y_fix;

    customBreak.check();
    auto_fit();
};

document.getElementById("load").onclick = () => {
    customBreak.check();
    auto_fit();
};


function submit_check(fin) {
    if (fin) {
        submit.disabled = false;
        draw_box(-2);
    } else {
        submit.disabled = true;
    }
};

function finish_check(index=-1) {
    finish.checked = true;
    for (let i = 0; i < set.length; i++) {
        if (i != index && !check[i].checked) {
            finish.checked = false;
        }
    }
    submit_check(finish.checked);
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
    if (customBreak.check()) auto_fit();

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

    for (let i = 0; i < set.length; i++) {
        if (set[i].checked) {
            box_li[i] = [x_min, y_min, x_max, y_max, 1];

            document.getElementById(`id_form-${i}-result_class`).value = 1;
            auto_set_box(i);

            check[i].disabled = false;
            check[i].checked = true;
            box_in[i].disabled = false;
            box_in[i].checked = true;
            checked[i].innerText = "チェック済み";

            draw_box(i);
        }
        console.log(box_li[i]);
    }
    finish_check();
};

canvas.addEventListener('touchmove', (e) => {
    if (!isDrawing) return;

    const touchObject = e.changedTouches[0];
    const coordinate = mobile_move(touchObject);
    
    width = coordinate[0] - startX;
    height = coordinate[1] - startY;

    draw_box(); // バウンディングボックスの描画

    // 矩形を青い線で描画
    ctx.strokeStyle = "blue";
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

    if (customBreak.check()) auto_fit();
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

    draw_box(); // バウンディングボックスの描画

    // 矩形を青い線で描画
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 7;
    ctx.strokeRect(startX, startY, width, height);
});


// マウスアップイベントのリスナーを追加
canvas.addEventListener("mouseup", () => {
    move_end();
});

// マウスアウトイベントのリスナーを追加
canvas.addEventListener("mouseout", () => {
    isDrawing = false;
});

function out_box(order) {
    for (let i = 0; i < set.length; i++) {
        if (i == order) set[i].checked = true;
        else set[i].checked = false;
    }
    draw_box(order); // バウンディングボックスの描画
};

// 選択したアイテムの座標を確定処理
function check_box(i) {
    if (check[i].checked) {
        document.getElementById(`id_form-${i}-box_x_min`).value = null;
        document.getElementById(`id_form-${i}-box_y_min`).value = null;
        document.getElementById(`id_form-${i}-box_x_max`).value = null;
        document.getElementById(`id_form-${i}-box_y_max`).value = null;
        
        checked[i].innerText = "チェック";
        finish.checked = false;
        submit.disabled = true;
    } else {
        checked[i].innerText = "チェック済み";

        auto_set_box(i);
        finish_check(i);
    
        console.log(`${i}. ${item_name[i]}`);
        console.log(` x_min: ${box_li[i][0].toFixed(4)} px`);
        console.log(` y_min: ${box_li[i][1].toFixed(4)} px`);
        console.log(` x_max: ${box_li[i][2].toFixed(4)} px`);
        console.log(` y_max: ${box_li[i][3].toFixed(4)} px`);
        console.log(` conf : ${box_li[i][4].toFixed(4) * 100} %`);
    }
    out_box(i);
};

// 選択したアイテムの座標を削除
function del_box(i) {
    if (box_in[i].checked) {
        box_li[i] = [0,0,0,0,0];
        document.getElementById(`id_form-${i}-result_class`).value = 0;
        document.getElementById(`id_form-${i}-box_x_min`).value = null;
        document.getElementById(`id_form-${i}-box_y_min`).value = null;
        document.getElementById(`id_form-${i}-box_x_max`).value = null;
        document.getElementById(`id_form-${i}-box_y_max`).value = null;
        
        check[i].disabled = true;
        check[i].checked = false;
        checked[i].innerText = "チェック";
        box_in[i].disabled = true;
        box_in[i].checked = false;
        finish.checked = false;
        submit.disabled = true;
    }
    out_box(i);
};

all_check.onclick = () => {
    var check_conf = threshold_conf;
    if (!model_check) check_conf = 0;
    for (let i = 0; i < set.length; i++) {
        if (box_li[i][4] > check_conf) {
            auto_set_box(i);
            check[i].checked = true;
            checked[i].innerText = "チェック済み";
        }
    }
    draw_box(-2);
    finish_check();
};

all_check_out.onclick = () => {
    for (let i = 0; i < set.length; i++) {
        if (check[i].checked) {
            document.getElementById(`id_form-${i}-box_x_min`).value = null;
            document.getElementById(`id_form-${i}-box_y_min`).value = null;
            document.getElementById(`id_form-${i}-box_x_max`).value = null;
            document.getElementById(`id_form-${i}-box_y_max`).value = null;
            
            check[i].checked = false;
            checked[i].innerText = "チェック";
        }
    }
    draw_box();
    finish_check();
};

submit.onclick = () => {
    for (let i = 0; i < set.length; i++) {
        if (checked[i].innerText != "チェック済み") {
            document.getElementById(`id_form-${i}-result_class`).value = 0;
        }
    }
};


window.onresize = () => {
    if (customBreak.check()) auto_fit();
};