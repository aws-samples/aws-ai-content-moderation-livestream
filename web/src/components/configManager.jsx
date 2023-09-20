import React from 'react';
import './configManager.css'
import { FetchData } from "../resources/data-provider";
import { CalculateTimeDifference } from "../resources/utility";
import { Button, ButtonDropdown, StatusIndicator, Link, Box, TextFilter, SpaceBetween, Tabs, Header, Modal, Cards, ColumnLayout, Spinner, Table } from '@cloudscape-design/components';
import ConfigDetail from './configDetail';
import Configs from './configs';

class ConfigManager extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            activeTab: this.props.activeTab === undefined || this.props.activeTab === null? "global": this.props.activeTab,
        };
    }

    handelConfigEdit = e => {
      this.props.onConfigEdit(e);
    }

    render() {
        return (
          <div className="rule">
            <Tabs activeTabId={this.state.activeTab}
              onChange={e=>(this.setState({activeTab: e.detail.activeTabId}))}
              tabs={[
                {
                  label: "Global Configs",
                  id: "global",
                  content: <Configs globalConfig={true} onConfigEdit={this.handelConfigEdit} />
                },
                {
                  label: "Channel Configs",
                  id: "channel",
                  content: <Configs globalConfig={false} onConfigEdit={this.handelConfigEdit} />
                }
              ]}
            />
          </div>
        );
    }
}

export default ConfigManager;