import React from 'react';
import './activeStreams.css'
import { FetchData } from "../resources/data-provider";
import { CalculateTimeDifference } from "../resources/utility";
import { Button, Badge, StatusIndicator, Link, Box, TextFilter, SpaceBetween, Pagination, Header, Modal, Cards, ColumnLayout, Spinner, Icon } from '@cloudscape-design/components';
import StreamDetail from './streamDetail';

class ActiveStreams extends React.Component {

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

            showWarningModal: false,
            stopStreamStatus: null,
            dismissWarningStatus: null
        };

        this.PAGE_SIZE = 10;
        this.TASK_LIMIT = 50;

        this.streamRef = React.createRef();
        
    }

    async componentDidMount() {
        // Call the API to fetch data
        if (this.state.items === null) {
          this.populateItems();    
        }

        this.timer = setInterval(
          () => this.populateItems(),
          10000,
        );
    }

    componentWillUnmount() {
      clearInterval(this.timer);
    }
    
    populateItems() {
        this.setState({status: "loading"});
        FetchData("/monitoring/streams", "post", {})
            .then((data) => {
                var resp = data.body;
                if (data.statusCode !== 200) {
                    this.setState( {status: null, alert: data.body});
                }
                else {
                    //console.log(resp);
                    if (resp !== null) {
                        var streams = JSON.parse(resp);
                        //console.log(streams);
                        this.setState(
                            {
                                items: streams,
                                status: "loaded",
                                pageItems: this.getCurrentPageItems(streams)
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
        if (filterText !== null & this.state.items !== undefined) {
          let result = []
          this.state.items.forEach((i) => {
            if (i.channel.name.toLowerCase().includes(e.detail.filteringText.toLowerCase())) {
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

    handelWarningDismiss = e => {
      var c = window.confirm("Do you want to dismiss the warning(s) and leave the stream running?");
      if (c === false)
        return;
      else {
        this.setState({dismissWarningStatus: "loading"});
        this.ackWarning("dismisswarning");
      }
    }

    handelStreamTermination = e => {
      var c = window.confirm("The stream will be terminated. Do you want to proceed?");
      if (c === false)
        return;
      else {
        this.setState({stopStreamStatus: "loading"});
        this.ackWarning("stopstream");
      }
    }

    async ackWarning(action) {
      if (this.state.selectedItems.length > 0){
        let payload = {
          "channel_arn": this.state.selectedItems[0].stream.channel_arn,
          "action": action
        };
          FetchData("/monitoring/acknowledge/", "post", payload)
          .then((data) => {
              var resp = data.body;
              if (data.statusCode !== 200) {
                  this.setState( {status: null, alert: data.body});
              }
              else {
                  //console.log(resp);
                  if (resp !== null) {
                      var result = JSON.parse(resp);
                      this.setState(
                          {
                              alert: result,
                              stopStreamStatus: "loaded",
                              dismissWarningStatus: "loaded",
                              showWarningModal: false
                          }
                      );
                  }
                this.populateItems();
              }
          })
          .catch((err) => {
              console.log(err.message);
              this.setState( {status: null, alert: err.message, stopStreamStatus: null, dismissWarningStatus: null});
          });    
      }
    }

    render() {
        return (
            <div class="streams">
              
              {this.state.showWarningModal?
                <Modal
                    onDismiss={() => {this.setState({showWarningModal: false}); }}
                    visible={this.state.showWarningModal}
                    header={this.state.selectedItems[0].channel.name}
                    description={"Channel Id:" + this.state.selectedItems[0].channel_id}
                    size="large"
                    >
                      <StreamDetail stream={this.state.selectedItems[0]}/>
                      <div className="button">
                        <Button 
                          variant='primary' 
                          onClick={this.handelStreamTermination}
                          loading={this.state.stopStreamStatus === "loading"}
                        >Terminate the stream
                        </Button>
                        <Button 
                          variant='normal' 
                          onClick={this.handelWarningDismiss}
                          loading={this.state.dismissWarningStatus === "loading"}
                        >Dismiss warning(s)
                        </Button>
                      </div>
                </Modal>:<div/>}
                <Cards
                  onSelectionChange={({ detail }) =>
                    this.setState({selectedItems: detail.selectedItems})
                  }
                  selectedItems={this.state.selectedItems}
                  ariaLabels={{
                    itemSelectionLabel: (e, n) => `select ${n.name}`,
                    selectionGroupLabel: "Stream selection"
                  }}
                  cardDefinition={{
                    header: item => item.channel.name,
                    sections: [
                      {
                        id: "channel_id",
                        content: item => 
                          <div className='card'>
                            {item.warnings !== undefined && item.warnings.length > 0? 
                              <div className='warning'onClick={
                                ({ detail }) => {
                                    this.setState({selectedItems: [item], showWarningModal: true});
                                }}>
                                <div className='message' >{item.warnings.length}&nbsp;Warning(s)!</div>
                              </div>:<div/>
                            }
                            <StatusIndicator type={item.stream.health === "HEALTHY"? "success":"error"}>{item.stream.health}</StatusIndicator> 
                            &nbsp;&nbsp;&nbsp;
                            <Badge color={item.stream.state === "LIVE"? "red":"blue"}>{item.stream.state}</Badge> 
                            <br/>
                            <div className='label'>Starts at</div> {CalculateTimeDifference(item.stream.start_time)}
                            <br/>
                            <div className='label'>View count</div> {item.stream.view_count}
                            <br/>
                            <img src={item.image_url} width="100%" alt="" />
                            <br/>
                          </div>
                      }
                    ]
                  }}
                  cardsPerRow={[
                    { cards: 3 },
                    { minWidth: 400, cards: 3 }
                  ]}
                  items={this.state.pageItems}
                  loadingText="Loading streams"
                  trackBy="channel_id"
                  visibleSections={["channel_id", "start_time","health", "state","view_count","image_url"]}
                  empty={
                    <Box
                      margin={{ vertical: "xs" }}
                      textAlign="center"
                      color="inherit"
                    >
                      <SpaceBetween size="m">
                      {this.state.status === "loading"?
                          <Spinner>Loading</Spinner>:
                          <b>No active streams</b>
                        }                      
                        </SpaceBetween>
                    </Box>
                  }
                  filter={
                    <TextFilter 
                      filteringPlaceholder="Find streams" 
                      filteringText={this.state.filterText} 
                      onChange={this.handleFilterChange} />
                  }
                  header={
                    <Header
                      counter={
                        (this.state.items ===undefined || this.state.items ===null)?"(0)": "(" + this.state.items.length + ")"
                      }
                      actions={
                        this.state.status === "loading"? <Spinner></Spinner>:<Button iconName='refresh' variant='icon' onClick={e=> this.populateItems()}></Button>
                      }
                    >
                      Live Streams
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

export default ActiveStreams;