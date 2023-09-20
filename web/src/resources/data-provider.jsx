import { Auth, API } from 'aws-amplify';

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
const API_KEY = process.env.REACT_APP_GENAI_DEMO_SERVICE_API_KEY;


/*
export default class DataProvider {
  getData(name) {
    return fetch(`../resources/${name}.json`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Response error: ${response.status}`);
        }
        return response.json();
      })
      .then(data => data.map(it => ({ ...it, date: new Date(it.date) })));
  }
}*/


async function FetchData(path, method="post", body=null, apiName='CmLiveStreamWebService') {
  const init = {
    headers: {
      Authorization: `Bearer ${(await Auth.currentSession())
        .getIdToken()
        .getJwtToken()}`,
      "x-api-key": API_KEY
    }
  };

  if (body !== null) {
    init["body"] = body;
  }

  switch(method.toLowerCase()) {
    case "get":
      return await API.get(apiName, path, init);
    case "post":
      return await API.post(apiName, path, init);
    case "put":
      return await API.put(apiName, path, init);
  }
  return null;
}

const ModerationCategories = [
  {
      name: "Explicit Nudity",
      items: [
          {name: "Nudity"},
          {name: "Graphic Male Nudity"},
          {name: "Graphic Female Nudity"},
          {name: "Sexual Activity"},
          {name: "Illustrated Explicit Nudity"},
          {name: "Adult Toys"}
      ],
  },
  {
      name: "Suggestive",
      items: [
          {name: "Female Swimwear Or Underwear"},
          {name: "Male Swimwear Or Underwear"},
          {name: "Partial Nudity"},
          {name: "Barechested Male"},
          {name: "Revealing Clothes"},
          {name: "Sexual Situations"},
      ]
  },
  {
      name: "Violence",
      items: [
          {name: "Graphic Violence Or Gore"},
          {name: "Physical Violence"},
          {name: "Weapon Violence"},
          {name: "Weapons"},
          {name: "Self Injury"}
      ]
  },
  {
    name: "Visually Disturbing",
    items: [
        {name: "Emaciated Bodies"},
        {name: "Corpses"},
        {name: "Hanging"},
        {name: "Air Crash"},
        {name: "Explosions And Blasts"}
    ]
  },
  {
    name: "Rude Gestures",
    items: [
        {name: "Middle Finger"}
    ]
  },
  {
    name: "Drugs",
    items: [
        {name: "Drug Products"},
        {name: "Drug Use"},
        {name: "Pills"},
        {name: "Drug Paraphernalia"}
      ]
  },
  {
    name: "Tobacco",
    items: [
        {name: "Tobacco Products"},
        {name: "Smoking"}
    ]
  },
  {
    name: "Alcohol",
    items: [
        {name: "Drinking"},
        {name: "Alcoholic Beverages"}
      ]
  },
  {
    name: "Gambling",
    items: [
        {name: "Gambling"}
      ]
  },
  {
    name: "Hate Symbols",
    items: [
        {name: "Nazi Party"},
        {name: "White Supremacy"},
        {name: "Extremist"}
    ]
  }
]
export {FetchData, ModerationCategories};