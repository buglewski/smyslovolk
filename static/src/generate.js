const URL_ROOT = document.getElementById("url").textContent;
const CONTAINER = document.getElementById("main");

async function generate(user_login, name, que = "", url = URL_ROOT) {
    const request = new Request(url + "gen/" + user_login + '/' + name + que);
    let response = await fetch(request);
    if (response.ok) {
      let json = await response.json();
      return json;
    } else {
      alert("Ошибка HTTP: " + response.status);
    }  
  }

  async function delete_generator(user_login, generator_name, url = URL_ROOT) {
    const request = new Request(url + "delete_generator/" + user_login + "/" + generator_name, {
      method : "DELETE"
    });
    let response = await fetch(request);
    if (response.ok) {
      return 0;
    } else {
      console.log("ERROR!");
      return 1;
    }  
  }

  async function get_generator(user_login, generator_name, url = URL_ROOT) {
    const request = new Request(url + "get_generator/" + user_login + "/" + generator_name);
    let response = await fetch(request);
    if (response.ok) {
      let json = await response.json();
      return json;
    } else {
      alert("Ошибка HTTP: " + response.status);
    }  
  }

  async function get_file(user_login, generator_name, filename, url = URL_ROOT) {
    const request = new Request(url + "get_file/" + user_login + "/" + generator_name + "/" + filename);
    let response = await fetch(request);
    if (response.ok) {
      let json = await response.json();
      return json;
    } else {
      return false;
    }  
  }

  async function save_file(user_login, generator_name, filename, text, url = URL_ROOT) {
    const request = new Request(url + "save_file/" + user_login + "/" + generator_name + "/" + filename, {
      method: 'PUT', 
      headers: { 
        'Content-type': 'application/json'
      }, 
      body: JSON.stringify({"text": text})
    });
      
    let response = await fetch(request);
    if (response.ok) {
      return 0;
    } else {
      console.log("ERROR!");
      return 1;
    } 
  }

  async function delete_file(user_login, generator_name, filename, url = URL_ROOT) {
    const request = new Request(url + "delete_file/" + user_login + "/" + generator_name + "/" + filename, {
      method: 'DELETE'
    });
      
    let response = await fetch(request);
    if (response.ok) {
      return 0;
    } else {
      console.log("ERROR!");
      return 1;
    } 
  }

  
  async function new_file(user_login, generator_name, filename, url = URL_ROOT) {
    const request = new Request(url + "new_file/" + user_login + "/" + generator_name + "/" + filename, {
      method: 'POST'
    });
      
    let response = await fetch(request);
    if (!response.ok) {
      console.log("ERROR!");
    } 
    return 0;
  }

  async function create_card(generator, page_of_generator = false, container = CONTAINER, url = URL_ROOT){
    const col = document.createElement("div"); if (!page_of_generator) col.classList.add("col-sm-6", "mb-3", "mb-sm-0", "meow"); container.appendChild(col);
    
    const card = document.createElement("div"); card.classList.add("card"); col.appendChild(card);
    const card_header = document.createElement("div"); card_header.classList.add("card-header"); card.appendChild(card_header);
    const card_name = document.createElement("a"); card_name.classList.add("cardname"); card_header.appendChild(card_name);
    const card_user = document.createElement("a"); card_user.classList.add("carduser"); card_header.appendChild(card_user);

    const card_body = document.createElement("div"); card_body.classList.add("card-body"); card.appendChild(card_body);
    const card_title = document.createElement("h5"); card_title.classList.add("card-title"); card_body.appendChild(card_title);
    const card_title_a = document.createElement("a");  card_title.appendChild(card_title_a);

    const card_subtitle = document.createElement("h6"); card_subtitle.classList.add("card-title", "meow"); card_body.appendChild(card_subtitle);
    const card_text = document.createElement("p"); card_text.classList.add("card-text", "meow"); card_body.appendChild(card_text);
    
    args = [];

    if (generator.mod == "py_generic"){
      let metadata = await get_file(generator.user_login, generator.name, generator.name + ".json");
      if (metadata){
        metadata = JSON.parse(metadata);
        console.log(metadata);
        for (i = 0; i < metadata.length; ++i){
          let row = document.createElement("div"); row.classList.add("row"); card_body.appendChild(row);
          let label = document.createElement("label"); label.classList.add("col-sm-6", "col-form-label"); row.append(label);
          let divinput = document.createElement("div"); divinput.classList.add("col-sm-6"); row.append(divinput);
          let input = document.createElement("input"); divinput.append(input); input.type = "text";
          //let divcom = document.createElement("div"); divcom.classList.add("col-sm-2"); row.append(divcom);
          if (metadata[i].name) label.textContent = metadata[i].name; else label.textContent = "Аргумент " + (i+1);
          if (metadata[i].default) input.value = metadata[i].default;
          if (metadata[i].req){
            if (metadata[i].req == "int") input.type = "number";
          }
          console.log(input.value)
          args.push(input);
        }
      }
    }

    const card_generate = document.createElement("button"); card_body.appendChild(card_generate);

    card_name.textContent = generator.name;
    card_user.textContent = generator.user_login;
    card_title_a.textContent = generator.title;
    card_subtitle.textContent = generator.description;

    card_name.href = url + generator.user_login + '/' + generator.name + '/edit';
    card_title_a.href = url + generator.user_login + '/' + generator.name;
    
    card_generate.textContent = "Сгенерировать";

    card_generate.onclick = async function onk(){
      card_text.textContent = "Waiting...";
      que = "?";
      for (i = 0; i < args.length; ++i){
        que += "args=" + args[i].value + "&";
      }
      let g = await generate(generator.user_login, generator.name, que);
      console.log(g);
      card_text.textContent = g[0];
    };
  }
