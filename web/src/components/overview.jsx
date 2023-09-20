import React from 'react';
import './overview.css'
import diagram from '../static/architecture.png'
import { Button, TextContent } from '@cloudscape-design/components';

class Overview extends React.Component {

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
            stopStreamStatus: null
        };

        this.PAGE_SIZE = 10;
        this.TASK_LIMIT = 50;

    }


    render() {
        return (
            <div className="overview">
                <TextContent>
                    <h1>AWS AI moderation - IVS live stream moderation dashboard</h1><br/>

                    <p>
                        This sample solution integrates with Amazon IVS by reading thumbnail images from an S3 bucket and sending images to the Rekognition image moderation API. It provides choices for automatic stream termination and HITL (human-in-the-loop) review. You can configure rules for the system to automatically halt streams based on conditions. It also includes a light human review portal, empowering moderators to monitor streams, manage violation alerts, and terminate streams when necessary.
                    </p>
                    <ul>
                    <li>Utilize the <Button variant='inline-link' onClick={e=>this.props.onNavigate("activestreams")}>Monitoring Dashboard</Button> page to observe active streams with near-real-time warnings. Take necessary action to either terminate the stream or dismiss the warnings.</li>
                    <li>Tailor moderation rules through the <Button variant='inline-link' onClick={e=>this.props.onNavigate("config")}>Manage Configurations</Button> pages. This feature empowers you to establish global settings applicable across multiple channels or define specific configurations for individual channels.</li>
                    </ul>
                    <br/>
                    <img src={diagram} alt="system architecture" className="diagram"></img>
                </TextContent>
            </div>
        );
    }
}

export default Overview;