import { useState, useRef } from "react";
import Header from "@cloudscape-design/components/header";
import * as React from "react";
import Alert from "@cloudscape-design/components/alert";
import {withAuthenticator} from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import {Navigation} from './components/commons/common-components';
import { AppLayout } from '@cloudscape-design/components';
import TopNavigation from "@cloudscape-design/components/top-navigation";
import logo from './static/aws_logo.png'
import { BreadcrumbGroup, Link, SpaceBetween } from '@cloudscape-design/components';
import ActiveStreams from './components/activeStreams'
import Overview from './components/overview'
import ConfigManager from "./components/configManager";
import ConfigDetail from './components/configDetail';

const ITEMS = [
  {
    type: "link",
    text: "Overview",
    id:"overview",
    href:"#/overview",
  },
  {
    type: "link",
    text: "Monitoring Dashboard", 
    id:"activestreams", 
    href:"#/activestreams",
  },
  {
    type: "link",
    id:"config", 
    text: 'Manage Configurations', 
    href:"#/config"
  }
]

const App = ({ signOut, user }) => {
  const [currentPage, setCurrentPage] = useState("overview");
  const [currentBreadcrumb, setCurrentBreadcrumb] = useState({"id":"overview", "text": "Overview" });
  const [navigationOpen, setNavigationOpen] = useState(true);
  const [activeNavHref, setActiveNavHref] = useState("#/overview");
  const [displayTopMenu, setDisplayTopMenu] = useState(window.self == window.top);
  const [currentConfig, setCurrentConfig] = useState(null);
  const [currentConfigTab, setCurrentConfigTab] = useState(null);

  const appLayout = useRef();

  const [selectedItems, setSelectedItems] = useState([]); 

  const handleItemClick = event => {
    setSelectedItems([]);
  }

  const onSelectionChange = event => {
    setSelectedItems(event.selectedItems);
  }

  const handleNavigationChange = () => {
    setNavigationOpen(!navigationOpen);
  }

  const handleNavItemClick = e => {
    setCurrentPage(e.detail.id);

    let nav = findItemById(e.detail.id);
    if (nav !== null)
      setCurrentBreadcrumb({"id":e.detail.id, "text": nav.text })
    setActiveNavHref("#/"+e.detail.id);
  }

  function findItemById(id) {
    for (let g = 0; g < ITEMS.length; g++) {
      //for (let i = 0; i < ITEMS[g].items.length; i++) {
        //if (ITEMS[g].items[i].id === id)
        //return ITEMS[g].items[i];
        if (ITEMS[g].id === id)
          return ITEMS[g];
      //}
    }
    return null;
  }

  const handleTopClick = e => {
    //console.log(e);
    setCurrentPage("overview");
    setActiveNavHref("#/overview")
    setNavigationOpen(true);
  }

  const handelConfigEdit = e =>{
    setCurrentConfig(e);
    setCurrentPage("configdetail");
  }

  const handleConfigEditCancel = (source) => {
    setCurrentConfig(null);
    setCurrentPage("config");
    setCurrentConfigTab(source)
  }
    return (
      <div>{displayTopMenu?
      <TopNavigation      
        identity={{
          href: "#",
          title: "AWS AI Content Moderation Live Stream",
          logo: {
            src: logo,
            alt: "AWS"
          },
          onFollow: handleTopClick   
        }}
        utilities={[
          {
            type: "menu-dropdown",
            text: user.username,
            description: user.email,
            iconName: "user-profile",
            onItemClick: signOut,
            items: [
              { type: "button", id: "signout", text: "Sign out"}
            ]
          }
        ]}
        i18nStrings={{
          searchIconAriaLabel: "Search",
          searchDismissIconAriaLabel: "Close search",
          overflowMenuTriggerText: "More",
          overflowMenuTitleText: "All",
          overflowMenuBackIconAriaLabel: "Back",
          overflowMenuDismissIconAriaLabel: "Close menu"
        }}
      />:<div/>}
      <AppLayout
        headerSelector="#header"
        ref={appLayout}
        contentType="table"
        navigationOpen={navigationOpen}
        onNavigationChange={handleNavigationChange}
        navigation={
          <Navigation 
            onFollowHandler={handleNavItemClick}
            selectedItems={["overview"]}
            activeHref={activeNavHref}
            items={ITEMS} 
          />}
        breadcrumbs={
          <BreadcrumbGroup 
            items={[{ "type": 'label', "text": 'Home'}, currentBreadcrumb]}
          />
        }
        toolsHide={true}
        content={
          currentPage === "activestreams"?<ActiveStreams />:
          currentPage === "config"?<ConfigManager onConfigEdit={handelConfigEdit} activeTab={currentConfigTab} />:
          currentPage === "configdetail"?<ConfigDetail config={currentConfig} onCancel={handleConfigEditCancel} />:
           <Overview onNavigate={e=>{
            setCurrentPage(e);
           }}/>
        }
      >
    </AppLayout>
    </div>
  );
}
export default withAuthenticator(App);
