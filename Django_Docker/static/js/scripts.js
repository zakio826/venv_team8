/*!
* Start Bootstrap - Modern Business v5.0.7 (https://startbootstrap.com/template-overviews/modern-business)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-modern-business/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project



const BREAKPOINT = {
    "xxl": 1400,
    "xl" : 1200,
    "lg" : 992,
    "md" : 768,
    "sm" : 576,
};

let class_width = window.innerWidth;

// bootstrapでのデフォルトのブレークポイントで発火
window.onresize = () => {
    let window_w = window.innerWidth;

    if      (class_width != BREAKPOINT["xxl"] && window_w >= BREAKPOINT["xxl"])                                class_width = BREAKPOINT["xxl"];
    else if (class_width != BREAKPOINT["xl"]  && window_w >= BREAKPOINT["xl"] && window_w < BREAKPOINT["xxl"]) class_width = BREAKPOINT["xl"];
    else if (class_width != BREAKPOINT["lg"]  && window_w >= BREAKPOINT["lg"] && window_w < BREAKPOINT["xl"])  class_width = BREAKPOINT["lg"];
    else if (class_width != BREAKPOINT["md"]  && window_w >= BREAKPOINT["md"] && window_w < BREAKPOINT["lg"])  class_width = BREAKPOINT["md"];
    else if (class_width != BREAKPOINT["sm"]  && window_w <  BREAKPOINT["md"])                                 class_width = BREAKPOINT["sm"];
    else return;

    console.log("\ntransition_class: " + Object.keys(BREAKPOINT).find((key) => BREAKPOINT[key] == class_width));

    // let block_js = document.getElementById("block_js");
    // if (block_js.innerHTML) transition_class();
};