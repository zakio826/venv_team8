
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const image = document.getElementById("image");
const preview = document.getElementById("preview");

const set = document.getElementsByName("set");
const box_in = document.getElementsByName("box");
const finish = document.getElementById("finish");
const submit = document.getElementById("submit");
const box_list = document.getElementById("box_list");
const create = document.getElementById("create").innerText;

const check_list = document.getElementById("check_list");
const switch_width = document.getElementById("switch_width");

const box_x_min = Number(document.getElementById("box_x_min").innerText);
const box_y_min = Number(document.getElementById("box_y_min").innerText);
const box_x_max = Number(document.getElementById("box_x_max").innerText);
const box_y_max = Number(document.getElementById("box_y_max").innerText);

const item_box = Number(document.getElementById("item_box").innerText);
const confirmation = document.getElementById("confirmation");

const x_fix = box_x_max - box_x_min;
const y_fix = box_y_max - box_y_min;

export {
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
};