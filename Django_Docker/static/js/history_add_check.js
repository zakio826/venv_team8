import {
    canvas,
    ctx,
    image,
    preview,

    set,
    box_in,
    finish,
    submit,
    box_list,
    create,

    check_list,
    switch_width,

    box_x_min,
    box_y_min,
    box_x_max,
    box_y_max,

    item_box,
    confirmation,

    x_fix,
    y_fix, 
} from "{% static 'js/history_add_import.js' %}";

const model_check = document.getElementById("model_check").innerText;

const check = document.getElementsByName("check");
const checked = document.getElementsByName("checked");

const check_ctrl = document.getElementById("check_ctrl");
const all_check = document.getElementById("all_check");
const all_check_out = document.getElementById("all_check_out");

// キャンバスサイズを初期化
canvas.width = x_fix;
canvas.height = y_fix;

let x_fit = canvas.width / x_fix;
let y_fit = canvas.height / y_fix;

// 描画状態を管理するフラグと座標を初期化
let isDrawing = false;
let startX, startY, width, height;
let x_min, x_max, y_min, y_max;

// アイテム名とバウンディングボックスの座標を初期化
let item_name = [];
let box_li = [];
for (let i = 0; i < set.length; i++) {
    item_name[i] = document.getElementById(`item_${i}_name`).innerText;

    // アイテムの座標がある場所
    if (item_box >= 2 && document.getElementById(`item_${i+1}_x_min`).innerText != "None") {
        box_li[i] = [
            Number(document.getElementById(`item_${i+1}_x_min`).innerText),
            Number(document.getElementById(`item_${i+1}_y_min`).innerText),
            Number(document.getElementById(`item_${i+1}_x_max`).innerText),
            Number(document.getElementById(`item_${i+1}_y_max`).innerText),
            Number(document.getElementById(`item_${i+1}_conf`).innerText),
        ];

        document.getElementById(`id_form-${i}-result_class`).value = 0;

        if (model_check == "False") box_li[i][4] = threshold_conf;

        if (box_li[i][4] > threshold_conf) {
            document.getElementById(`id_form-${i}-result_class`).value = 2;
        } else if (box_li[i][4] > 0) {
            document.getElementById(`id_form-${i}-result_class`).value = 1;
        }

        check[i].disabled = false;
        box_in[i].disabled = false;
        box_in[i].checked = true;

    } else {
        box_li[i] = [0,0,0,0,0];
        document.getElementById(`id_form-${i}-result_class`).value = 0;
    }
}
console.log(item_name);


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
function draw_box(order) {

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


// 画面サイズに合わせて要素を最適化
function auto_fit() {
    canvas.width = preview.getBoundingClientRect().width.toFixed();
    canvas.height = canvas.width * (y_fix / x_fix);

    x_fit = canvas.width / x_fix;
    y_fit = canvas.height / y_fix;

    for (let i = 0; i < set.length; i++) {
        box_li[i][0] *= x_fit;
        box_li[i][1] *= y_fit;
        box_li[i][2] *= x_fit;
        box_li[i][3] *= y_fit;
    }

    var max_h = 200;
    if (window.innerWidth >= 768) {
        var max_h = canvas.height - check_ctrl.getBoundingClientRect().height - 16;
        switch_width.style.width = "auto";
        check_list.style.marginTop = "auto";
    } else {
        switch_width.style.width = 210 * set.length;
        check_list.style.marginTop = "30px";
    }
    check_list.style.height = max_h;

    draw_box(-1);

    console.log(`preview.width:  ${preview.getBoundingClientRect().width} px`);
    console.log(`preview.height: ${preview.getBoundingClientRect().height} px`);
    console.log(`canvas.width:  ${canvas.width} px`);
    console.log(`canvas.height: ${canvas.height} px`);
    
};


// 画像の読み込みが完了したらキャンバスに描画
image.onload = () => {
    canvas.width = image.width;
    canvas.height = image.height;

    x_fit = canvas.width / x_fix;
    y_fit = canvas.height / y_fix;

    auto_fit();
    draw_box(-1);
};

// マウスダウンイベントのリスナーを追加
canvas.addEventListener("mousedown", (e) => {
    auto_fit();
    isDrawing = true;
    startX = e.clientX - canvas.getBoundingClientRect().left;
    startY = e.clientY - canvas.getBoundingClientRect().top;
});

// マウスムーブイベントのリスナーを追加
canvas.addEventListener("mousemove", (e) => {
    if (!isDrawing) return;

    const x = e.clientX - canvas.getBoundingClientRect().left;
    const y = e.clientY - canvas.getBoundingClientRect().top;

    width = x - startX;
    height = y - startY;

    draw_box(-1); // バウンディングボックスの描画

    // 矩形を青い線で描画
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 7;
    ctx.strokeRect(startX, startY, width, height);
});

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

// マウスアップイベントのリスナーを追加
canvas.addEventListener("mouseup", () => {
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
});

// マウスアウトイベントのリスナーを追加
canvas.addEventListener("mouseout", () => {
    isDrawing = false;
});






// bootstrapでのデフォルトのブレークポイントで発火
function transition_class () {
    auto_fit();
    draw_box(-1);
};