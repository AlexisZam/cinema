import html from "./index.html";
import "./index.css";

function cosineDistanceBetweenPoints(lat1, lon1, lat2, lon2) {
  const R = 6371e3;
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const deltaP = p2 - p1;
  const deltaLon = lon2 - lon1;
  const deltaLambda = (deltaLon * Math.PI) / 180;
  const a =
    Math.sin(deltaP / 2) * Math.sin(deltaP / 2) +
    Math.cos(p1) *
      Math.cos(p2) *
      Math.sin(deltaLambda / 2) *
      Math.sin(deltaLambda / 2);
  const d = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)) * R;
  return d;
}

const WEEKDAYS = [
  "Κυριακή",
  "Δευτέρα",
  "Τρίτη",
  "Τετάρτη",
  "Πέμπτη",
  "Παρασκευή",
  "Σάββατο",
];
const WEEKDAYS_CINEMA = [
  "Πέμπτη",
  "Παρασκευή",
  "Σάββατο",
  "Κυριακή",
  "Δευτέρα",
  "Τρίτη",
  "Τετάρτη",
];

let lat, lng;

navigator.geolocation.getCurrentPosition(
  async ({ coords: { latitude, longitude } }) => {
    [lat, lng] = [latitude, longitude];
    await submit();
  },
  ({ code, message }) => console.warn(`(${code}): ${message}`),
  { enableHighAccuracy: true }
);

const today = new Date().toISOString().split("T")[0];

function getLastThursday() {
  const date = new Date();
  const currentDay = date.getDay();
  const lastThursday = new Date(date);
  lastThursday.setDate(date.getDate() - ((currentDay + 3) % 7));
  return lastThursday;
}

async function submit() {
  const form = document.querySelector("form");
  const formData = new FormData(form);

  // console.log(formData.entries()[0]);
  let query = Array.from(formData)
    .map(([name, value]) => `${name}=${value}`)
    .join("&");

  //   if (lat && lng) query += `&lat=${lat}&lng=${lng}`;

  // const data = {
  //     name: input.name,
  //     value: input.value
  // };
  // const response = await fetch("/api", {
  //     method: 'POST',
  //     headers: {
  //         'Content-Type': 'application/json'
  //     },
  //     body: JSON.stringify(data)
  // })
  const url = `/api?${query}`;
  console.log(url);
  const response = await fetch(url);
  const json = await response.json();

  function setTime(time) {
    const li = document.createElement("li");
    li.textContent = time.time.split(":").slice(0, -1).join(":");
    // if (time.cinobo_pass) li.classList.add("cinobo");
    return li;
  }

  function setDate(date) {
    const weekday = WEEKDAYS[new Date(date.date).getDay()];

    const h3 = document.createElement("h3");
    h3.textContent = weekday;

    const ol = document.createElement("ol");
    ol.classList.add("time");
    date.times.forEach((time) => {
      time = setTime(time);
      ol.appendChild(time);
    });

    const li = document.createElement("li");
    li.appendChild(h3);
    li.appendChild(ol);

    return li;
  }

  function setHall(hall) {
    const a = document.createElement("a");
    a.href = hall.url;
    a.target = "_blank";
    a.textContent = hall.name;

    const h2 = document.createElement("h2");
    h2.appendChild(a);

    const ol = document.createElement("ol");
    ol.classList.add("date");
    hall.dates.forEach((date) => {
      date = setDate(date);
      ol.appendChild(date);
    });

    const li = document.createElement("li");
    li.appendChild(h2);
    li.appendChild(ol);

    return li;
  }

  function setMovie(movie) {
    let name = movie.title;
    if (movie.original_title) name += ` (${movie.original_title})`;

    const a = document.createElement("a");
    a.href = movie.url;
    a.target = "_blank";
    a.textContent = name;

    const rating = document.createElement("span");
    rating.textContent = `${Math.round(movie.rating * 10) / 10}`;
    if (movie.votes <= 10000) rating.classList.add("limited");

    const criticsRating = document.createElement("span");
    criticsRating.textContent = `${Math.round(movie.critics_rating * 10) / 10}`;
    if (movie.critics_votes <= 10) criticsRating.classList.add("limited");

    const h1 = document.createElement("h1");
    h1.appendChild(a);
    h1.appendChild(rating);
    h1.appendChild(criticsRating);

    const ol = document.createElement("ol");
    ol.classList.add("hall");

    if (lat && lng) {
      movie.halls = movie.halls.sort((a, b) => {
        const aDistance = cosineDistanceBetweenPoints(lat, lng, a.lat, a.lng);
        const bDistance = cosineDistanceBetweenPoints(lat, lng, b.lat, b.lng);
        return aDistance - bDistance;
      });
    }

    movie.halls.forEach((hall) => {
      hall = setHall(hall);
      ol.appendChild(hall);
    });

    const li = document.createElement("li");
    li.appendChild(h1);
    li.appendChild(ol);

    return li;
  }

  const ol = document.createElement("ol");
  ol.classList.add("movie");

  console.log(json.movies);
  json.movies.forEach((movie) => {
    movie = setMovie(movie);
    ol.appendChild(movie);
  });

  const output = document.querySelector("#output");
  if (output.firstChild) {
    output.replaceChild(ol, output.firstChild);
  } else {
    output.appendChild(ol);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document.body.innerHTML = html;

  const dates = document.querySelector("#dates");

  WEEKDAYS_CINEMA.forEach((weekday, index) => {
    const label = document.createElement("label");
    label.htmlFor = weekday;
    label.textContent = weekday;
    dates.appendChild(label);
    const input = document.createElement("input");
    input.id = weekday;
    input.type = "checkbox";
    input.name = "date";
    const day = getLastThursday();
    day.setDate(day.getDate() + index);
    input.value = day.toISOString().split("T")[0];
    if (day < new Date(today)) {
      input.checked = false;
      input.disabled = true;
    } else {
      input.checked = true;
    }
    dates.appendChild(input);
  });

  const minTimeLabel = document.createElement("label");
  minTimeLabel.htmlFor = "min_time";
  minTimeLabel.textContent = "Από";
  const minTime = document.createElement("input");
  minTime.type = "time";
  minTime.value = "00:00";
  minTime.name = "min_time";
  minTime.step = "300";
  const maxTimeLabel = document.createElement("label");
  maxTimeLabel.htmlFor = "max_time";
  maxTimeLabel.textContent = "έως";
  const maxTime = document.createElement("input");
  maxTime.type = "time";
  maxTime.name = "max_time";
  maxTime.value = "23:55";
  //   maxTime.step = "300";
  const times = document.querySelector("#times");
  times.appendChild(minTimeLabel);
  times.appendChild(minTime);
  times.appendChild(maxTimeLabel);
  times.appendChild(maxTime);

  const ratingLabel = document.createElement("label");
  ratingLabel.htmlFor = "min_rating";
  ratingLabel.textContent = "Ελάχιστη βαθμολογία κοινού";

  const rating = document.createElement("input");
  rating.type = "range";
  rating.name = "min_rating";
  rating.min = "0";
  rating.max = "10";
  rating.step = "0.1";
  rating.value = "7";

  rating.oninput = ({ target }) => {
    const ratingOutput = document.querySelector("#rating-output");
    ratingOutput.textContent = (<HTMLInputElement>target).value;
  };

  const ratingOutput = document.createElement("output");
  ratingOutput.id = "rating-output";
  ratingOutput.textContent = rating.value;

  const criticsRatingLabel = document.createElement("label");
  criticsRatingLabel.htmlFor = "min_rating";
  criticsRatingLabel.textContent = " και κριτικών";

  const criticsRating = document.createElement("input");
  criticsRating.type = "range";
  criticsRating.name = "min_critics_rating";
  criticsRating.min = "0";
  criticsRating.max = "5";
  criticsRating.step = "0.1";
  criticsRating.value = "3";

  criticsRating.oninput = ({ target }) => {
    const ratingOutput = document.querySelector("#critics-rating-output");
    ratingOutput.textContent = (<HTMLInputElement>target).value;
  };

  const critcsRatingOutput = document.createElement("output");
  critcsRatingOutput.id = "critics-rating-output";
  critcsRatingOutput.textContent = criticsRating.value;

  const ratingDiv = document.querySelector("#rating");
  ratingDiv.appendChild(ratingLabel);
  ratingDiv.appendChild(rating);
  ratingDiv.appendChild(ratingOutput);
  ratingDiv.appendChild(criticsRatingLabel);
  ratingDiv.appendChild(criticsRating);
  ratingDiv.appendChild(critcsRatingOutput);

  const inputs = document.querySelectorAll("input");

  inputs.forEach((input) => {
    input.addEventListener("change", submit);
  });

  await submit();

  // document.querySelectorAll('li').forEach(li => {
  //     const button = document.createElement('button');
  //     button.textContent = '-';
  //     button.addEventListener('click', event => {
  //         event.target.classList.toggle('collapsed');
  //     });
  //     li.appendChild(button);
  // });
});
