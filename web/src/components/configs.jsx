import React from 'react';
import './channels.css'
import { FetchData } from "../resources/data-provider";
import { CalculateTimeDifference } from "../resources/utility";
import { Button, Badge, StatusIndicator, Link, Box, TextFilter, SpaceBetween, Pagination, Header, Modal, Cards, ColumnLayout, Spinner, ExpandableSection } from '@cloudscape-design/components';
import StreamDetail from './streamDetail';
import ConfigDetail from './configDetail';

class Configs extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            status: "loading", // null, loading, loaded
            alert: null,
            selectedItems: [],
            pageItems: [],
            items: null,
            currentPageIndex: 1,
            isDescending: false,
            filterText: null,

            showStreamModal: false,
            showRuleModal: false,
            selectedItemStreamExpanded: false,
            stopStreamStatus: null,
            dismissWarningStatus: null,
            showDeleteConfirmModal: false,
            globalConfig: this.props.globalConfig === undefined ? true: this.props.globalConfig
        };

        this.PAGE_SIZE = 10;
        this.TASK_LIMIT = 50;
        
    }

    async componentDidMount() {
        // Call the API to fetch data
        if (this.state.items === null) {
          this.populateItems();    
        }

    }

    populateItems() {
        this.setState({status: "loading"});
        FetchData("/rules-engine/configs", "post", {"global_flag": this.state.globalConfig})
            .then((data) => {
                var resp = data.body;
                if (data.statusCode !== 200) {
                    this.setState( {status: null, alert: data.body});
                }
                else {
                    if (resp !== null) {
                        var result = JSON.parse(resp);
                        this.setState(
                            {
                                items: result,
                                status: "loaded",
                                pageItems: this.getCurrentPageItems(result)
                            }
                        );
                    }
                }
            })
            .catch((err) => {
                console.log(err.message);
                this.setState( {status: null, alert: err.message});
            });    
    }

    getCurrentPageItems(items, curPage=this.state.currentPageIndex) {
        if (items === undefined || items === null || items.length === 0) return [];
        else {
          var result = [];
          items.forEach((i, index) => {
            //console.log(index, (curPage - 1) * this.PAGE_SIZE, curPage * this.PAGE_SIZE);
            if (index >= ((curPage - 1) * this.PAGE_SIZE) && index < curPage * this.PAGE_SIZE) {
              result.push(i);
            }
            return result;
          }, result)
        }
        return result;
      }

    handleFilterChange = e => {
        let filterText = e.detail.filteringText;
        this.setState({filterText: filterText});
        if (filterText !== null && this.state.items !== undefined) {
          let result = []
          this.state.items.forEach((i) => {
            if (i.name.toLowerCase().includes(e.detail.filteringText.toLowerCase())) {
              result.push(i);
            }
            return result;
          }, result)
          this.setState({pageItems: this.getCurrentPageItems(result)})
        }
    }
    
    handleRefresh = e => {
        this.populateItems();
    }

    handlePaginationChange = e => {
      this.setState({
        currentPageIndex: e.detail.currentPageIndex,
      });
      this.populateItems();
      
    }

    handelEditConfigClose = e => {
      this.setState({showRuleModal: false});
      this.populateItems();
    }

    handleDeleteRule = e => {
      console.log(this.state.selectedItems);
      this.setState({status: "loading"});
      FetchData("/rules-engine/config-delete", "post", {"channel_ids": this.state.selectedItems.map(c => c.channel_id)})
          .then((data) => {
              var resp = data.body;
              if (data.statusCode !== 200) {
                  this.setState( {status: null, alert: data.body});
              }
              else {
                  if (resp !== null) {
                      var result = JSON.parse(resp);
                      this.populateItems();
                      this.setState(
                          {
                              status: "loaded",
                              pageItems: this.getCurrentPageItems(this.state.items),
                              showDeleteConfirmModal: false
                          }
                      );
                  }
              }
          })
          .catch((err) => {
              console.log(err.message);
              this.setState( {status: null, alert: err.message, showDeleteConfirmModal: false});
          });   
    }

    handelEditConfig = e => {
      if (e !== null) {
        e.global_flag = this.state.globalConfig;
      }
      this.props.onConfigEdit(e);
    }

    handelConfigAdd = e =>{
      this.props.onConfigEdit({
        channel_id: null,
        global_flag: this.state.globalConfig,
        channel_name_regex: null,
        name: null,
        image: {
            api: "rekognition_image_moderation_api",
            sample_frequency_s: 60,
            ignore_similar: true,
            image_hash_threshold: 10,
            rules: []
        }
    });
    }

    render() {
        return (
            <div class="streams">
              <Modal
                  onDismiss={() => {this.setState({showDeleteConfirmModal: false}); }}
                  header={this.state.selectedItems.length > 0 ?this.state.selectedItems[0].name:""}
                  size="medium"
                  visible={this.state.showDeleteConfirmModal}
                  >
                  Would you like to delete the moderation rule for Channel:  {this.state.selectedItems.length > 0 ?this.state.selectedItems[0].name:""}?
                  <br/><br/>
                  <Button variant='primary' onClick={this.handleDeleteRule}>Confirm</Button>
                  <Button onClick={() => this.setState({showDeleteConfirmModal: false})}>Cancel</Button>
              </Modal>
                <Cards
                  onSelectionChange={({ detail }) =>
                    this.setState({selectedItems: detail.selectedItems})
                  }
                  selectedItems={this.state.selectedItems}
                  ariaLabels={{
                    itemSelectionLabel: (e, n) => `select ${n.name}`,
                    selectionGroupLabel: "Channel selection"
                  }}
                  cardDefinition={{
                    header: item => item.name,
                    sections: [
                      {
                        id: "arn",
                        content: item => 
                          <div className='card'>
                            {item.channel_name_regex !== undefined && item.channel_name_regex !== null?
                            <div><label>Channel Name Regex: {item.channel_name_regex}</label><br/><br/></div>:
                            <div><label>Channel Id: {item.channel_id}</label><br/></div>}
                            <label className='desc'>{item.description}</label><br/><br/>
                            
                            <Button iconAlign='right' 
                              onClick={
                                    ({ detail }) => {
                                        //this.setState({selectedItems: [item], showRuleModal: true});
                                        this.handelEditConfig(item);
                                    }}
                              >
                                    Edit
                            </Button>
                            <Button iconAlign='right' 
                              onClick={
                                    ({ detail }) => {
                                        this.setState({selectedItems: [item], showDeleteConfirmModal: true});
                                    }}
                              >
                                    Delete
                            </Button>    
                          </div>
                      }
                    ]
                  }}
                  cardsPerRow={[
                    { cards: 3 },
                    { minWidth: 400, cards: 3 }
                  ]}
                  items={this.state.pageItems}
                  loadingText="Loading configurations"
                  trackBy="channel_id"
                  empty={
                    <Box
                      margin={{ vertical: "xs" }}
                      textAlign="center"
                      color="inherit"
                    >
                      <SpaceBetween size="m">
                        {this.state.status === "loading"?
                          <Spinner>Loading</Spinner>:
                          <b>No configurations</b>
                        }
                      </SpaceBetween>
                    </Box>
                  }
                  filter={
                    <TextFilter 
                      filteringPlaceholder="Find configuration" 
                      filteringText={this.state.filterText} 
                      onChange={this.handleFilterChange} />
                  }
                  header={
                    <Header
                      counter={
                        (this.state.items ===undefined || this.state.items ===null)? "(0)": "(" + this.state.items.length + ")"
                      }
                      actions={
                      <Button onClick={this.handelConfigAdd}>Create Config</Button>}
                    >
                      {this.state.globalConfig? "Global": "Channel"} Configurations
                    </Header>
                  }
                  pagination={
                    <Pagination currentPageIndex={this.state.currentPageIndex} 
                      pagesCount={this.state.items !== null?Math.ceil(this.state.items.length/this.PAGE_SIZE,0): 1} 
                    />
                  }
                />
          </div>
        );
    }
}

export default Configs;