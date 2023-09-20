import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
      identityPoolId: process.env.REACT_APP_COGNITO_IDENTITY_POOL_ID,
      region: process.env.REACT_APP_COGNITO_REGION,
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolWebClientId: process.env.REACT_APP_COGNITO_USER_POOL_CLIENT_ID,
    },
  API: {
      endpoints: [
          {
              name: "CmLiveStreamWebService",
              endpoint: process.env.REACT_APP_APIGATEWAY_BASE_URL,
          },
      ]
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));


root.render(
    <App />
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();