import React from 'react';
import './streamDetail.css'
import { CalculateTimeDifference } from "../resources/utility";
import { Badge, StatusIndicator, ColumnLayout } from '@cloudscape-design/components';

class StreamDetail extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            status: "loading", // null, loading, loaded
            streamExpanded: false,
        };

        this.streamRef = React.createRef();
    }
    
    managerStream (action) {
      if (window.IVSPlayer.isPlayerSupported) {
          const player = window.IVSPlayer.create();
          let domElement = this.streamRef.current;
          console.log(domElement);
          if (domElement !== undefined && domElement !== null) {
            player.attachHTMLVideoElement(domElement.id);
            player.load(this.props.stream.playbackUrl);
            if (action === "on") player.play();
            else player.pause();
          }
        }
    }

    render() {
        return (
              <div className="stream">
                {this.props.stream !== null?
                <div>
                  <Badge color={this.props.stream.stream.state === "LIVE"? "red":"blue"}>{this.props.stream.stream.state}</Badge> 
                  <br/>
                  {this.props.stream.warnings !== undefined && this.props.stream.warnings !== null?
                    this.props.stream.warnings.map((warning) => (
                    <div className="meta">
                      <ColumnLayout columns={2}>
                        <img className="thumbnail" src={warning.image.url} width="100%"></img>
                        <div>
                          <div className="descrption">{warning.result[0].description}</div>
                          <div className="descrption">
                          {warning.severity === "HIGH"?<Badge color="red">Exceed SLA</Badge>:<div/>}&nbsp;
                          {CalculateTimeDifference(warning.timestamp)}
                          </div>
                        </div>
                      </ColumnLayout>
                    </div>
                  )):<div/>}
                  <StatusIndicator type={this.props.stream.stream.health === "HEALTHY"? "success":"error"}>{this.props.stream.stream.health}</StatusIndicator> 
                  <br/>
                  <div className='label'>Stream Starts at</div> {CalculateTimeDifference(this.props.stream.stream.start_time)}
                  <br/>
                  <div className='label'>View count</div> {this.props.stream.stream.view_count}
                </div>:<div/>}
            </div>
        );
    }
}

export default StreamDetail;