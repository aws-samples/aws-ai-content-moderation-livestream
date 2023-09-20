import React from 'react';
import './configDetail.css'
import './dropdowntree.css'
import { FetchData, ModerationCategories } from "../resources/data-provider";
import { Button, FormField, Input, ButtonDropdown, Box, SpaceBetween, Alert, Header, Modal, TokenGroup, ColumnLayout, Autosuggest, Table, Container, Checkbox, Textarea, ExpandableSection } from '@cloudscape-design/components';
import { v4 as uuidv4 } from 'uuid';
import Slider from '@mui/material/Slider';
import DropdownTreeSelect from 'react-dropdown-tree-select';

class ConfigDetail extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            alert:null,
            alertType:"Info",
            status: null, // null, loading, loaded
            selectedImageRules: [],

            config: this.props.config,

            showEditRuleModal: false,
            submitImageRuleFlag: false,
            ruleAlert: null,
            moderationCategories: this.populateModerationCategories(),

            currentRuleName: null,
            currentCategories: null,
            currentRuleConfidence: 60,
            currentRuleAutoStop: true,
            currentSearchCategoryText: "",

            invalidRuleName: false,
            invalidRuleCategories: false,

            invalidConfig: {
              invalidConfigName: false,
              invalidRegex: false,
              invalidImageFreqency: false,
              invalidSimilarThreshold: false,
              invalidPriority: false,
              invalidImageRules: false
            },
            imageExpanded: true,
        };
    }

    resetStates() {
      this.setState(
        {
          alert:null,
          alertType:"Info",
          status: null, // null, loading, loaded
          selectedImageRules: [],

          config: this.props.config,

          showEditRuleModal: false,
          submitImageRuleFlag: false,
          ruleAlert: null,

          currentRuleName: null,
          currentCategories: null,
          currentRuleConfidence: 60,
          currentRuleAutoStop: true,
          currentSearchCategoryText: "",

          invalidRuleName: false,
          invalidRuleCategories: false,

          invalidConfig: {
            invalidConfigName: false,
            invalidRegex: false,
            invalidImageFreqency: false,
            invalidSimilarThreshold: false,
            invalidPriority: false,
            invalidImageRules: false
          },

          imageExpanded: true,
        }
      )
    }

    resetConfigValidation () {
      this.setState({invalidConfig: {
        invalidConfigName: false,
        invalidRegex: false,
        invalidImageFreqency: false,
        invalidSimilarThreshold: false,
        invalidPriority: false,
        invalidImageRules: false
      }});
    }

    constructImageRule() {
        return {
                id: uuidv4(),
                name: null,
                categories: null,
                confidence_threshold: 60,
                auto_stop: true
            }
    }

    componentDidUpdate(nextProps) {
      if (this.props !== nextProps) {
        this.setState({config: this.props.config});
      }        

    } 

    populateModerationCategories() {
        var result =[];
        for(var i=0; i< ModerationCategories.length; i++) {
          result.push({label: ModerationCategories[i].name, value: ModerationCategories[i].name})
          if (ModerationCategories[i].items !== undefined) {
            for(var j=0;j<ModerationCategories[i].items.length; j++) {
              result.push({label: " - " + ModerationCategories[i].items[j].name, value: ModerationCategories[i].items[j].name})
            }
          }
        }
        return result;
    }


    handleSaveImageRule = e=> {
        this.setState({invalidRuleName: false, invalidRuleCategories: false});

        var invalid = false;
        if(this.state.currentRuleName === null || this.state.currentRuleName.length === 0) {
            this.setState({invalidRuleName: true});
            invalid = true;
        }
        if (this.currentCategories === null || this.state.currentCategories.length === 0) {
            this.setState({invalidRuleCategories: true});
            invalid = true;
        }
            
        if (!invalid) {
          let config = this.state.config;
          let rule = config.image.rules.find(r=>r.id === this.state.selectedImageRules[0].id);
          if (rule === null || rule === undefined) {
            // new rule
            rule = {
              id: this.state.selectedImageRules[0].id
            }
            config.image.rules.push(rule);
          }
          rule.name = this.state.currentRuleName;
          rule.categories = this.state.currentCategories;
          rule.confidence_threshold = this.state.currentRuleConfidence;
          rule.auto_stop = this.state.currentRuleAutoStop;
          
          this.setState(
            {
              selectedImageRules: [rule],
              config: config,
              showEditRuleModal: false
            }
          )
        }
    }

    handleSumbit = e => {
      let config = this.state.config;

      if (config.channel_id === null) {
        // new config
        if (config.global_flag) config.channel_id = uuidv4();
        else if(this.props.channel_id !== null) config.channel_id = this.props.channel_id;
      }

      // Validation
      let invalidConfig = {
        invalidConfigName: config.name === null || config.name.length == 0,
        invalidRegex: config.global_flag === true && (config.channel_name_regex === null || config.channel_name_regex.length === 0),
        invalidImageFreqency: config.image.sample_frequency_s === null || isNaN(parseFloat(config.image.sample_frequency_s)),
        invalidSimilarThreshold: config.image.image_hash_threshold === null || isNaN(parseFloat(config.image.image_hash_threshold)),
        invalidPriority: config.global_flag === true && (config.priority === null || isNaN(parseFloat(config.priority))),
        invalidImageRules: config.image.rules.length == 0,
        invalidChannelId: !config.global_flag && config.channel_id === null
      }

      this.setState({invalidConfig: invalidConfig});
      if (invalidConfig.invalidConfigName 
        || invalidConfig.invalidRegex || invalidConfig.invalidImageFreqency 
        || invalidConfig.invalidSimilarThreshold || invalidConfig.invalidPriority 
        || invalidConfig.invalidImageRules) return;

      this.setState({status: "loading"});
      FetchData("/rules-engine/config-upsert", "post", {"config":config})
          .then((data) => {
              var resp = data.body;
              if (data.statusCode !== 200) {
                  this.setState( {status: null, alert: data.body});
              }
              else {
                  if (resp !== null) {
                      var result = JSON.parse(resp);
                      this.resetStates();
                      this.props.onCancel(this.state.config.global_flag?"global":"channel");
                  }
              }
          })
          .catch((err) => {
              console.log(err.message);
              this.setState( {status: null, alert: err.message, alertType: "Error"});
          });    
    }

    handelCancel = (e) => {
      var source = this.state.config.global_flag?"global":"channel";
      this.resetStates();
      this.props.onCancel(source);
    }

    render() {
        return (
              <div className="config">
                {this.state.alert !== null?
                  <div className="alert">
                  <Alert dismissible 
                    onDismiss={e => this.setState({alert: null})}
                    statusIconAriaLabel={this.state.alertType}
                    type={this.state.alertType.toLowerCase()}
                  >
                    {this.state.alert}
                  </Alert></div>:<div/>
                }
                <Container>
                  <ColumnLayout columns={2}>
                  <FormField
                      label="Config Name"
                      description="The name of the configuration."
                      stretch={true}
                    >
                      <Input 
                        onChange={({ detail }) => {
                            let config = this.state.config;
                            config.name = detail.value;
                            this.setState({config: config});
                            this.resetConfigValidation();
                        }}                         
                        defaultValue={this.props.channel_name}
                        value={this.state.config !==null && this.state.config!==undefined?this.state.config.name:""} 
                        invalid={this.state.invalidConfig.invalidConfigName}
                        />
                    </FormField>
                    <FormField
                      label="Description"
                      description="A description of the configuration."
                      stretch={true}
                    >
                      <Textarea 
                        onChange={({ detail }) => {
                            let config = this.state.config;
                            config.description = detail.value;
                            this.setState({config: config});
                        }}                         
                        defaultValue={this.props.channel_name}
                        value={this.state.config !==null && this.state.config!==undefined?this.state.config.description:""} 
                        />
                    </FormField>
                  </ColumnLayout>
                  {this.state.config.global_flag?
                    <ColumnLayout columns={2}>
                      <FormField
                        label="Channel name regex"
                        description="Regex apply to channel names. E.x, /.*/ apply to all the channels, /^ivs-/ apply to all the channel names start with 'ivs-'"
                        stretch={true}
                      >
                        <Input 
                          onChange={({ detail }) => {
                              let config = this.state.config;
                              config.channel_name_regex = detail.value;
                              this.setState({config: config});
                              this.resetConfigValidation();
                          }}                         
                          value={this.state.config !== undefined && this.state.config !==null?this.state.config.channel_name_regex:""} 
                          invalid={this.state.invalidConfig.invalidRegex}
                          />
                      </FormField>
                      <FormField
                        label="Priority"
                        description="This applies when there are multiple global rules for the same channel. A lower number means higher priority."
                        stretch={true}
                      >
                        <Input 
                          onChange={({ detail }) => {
                            var p = detail.value.length === 0? "": parseFloat(detail.value);
                            if (detail.value.length > 0 && isNaN(p)) return;
                              let config = this.state.config;
                              config.priority = p;
                              this.setState({config: config});
                              this.resetConfigValidation();
                          }}                         
                          value={this.state.config !== undefined && this.state.config !==null?this.state.config.priority:1} 
                          invalid={this.state.invalidConfig.invalidPriority}
                          />
                      </FormField>
                    </ColumnLayout>
                  :
                  <ColumnLayout columns={2}>
                    <FormField
                      label="Channel Id & Name"
                      description="The IVS channel ID can be located within the AWS IVS console. For example: QpVB4bfA1XIV"
                      stretch={true}
                    >
                      {this.channel_id === undefined || this.channel_id === null?
                      <Input 
                        onChange={({ detail }) => {
                            let config = this.state.config;
                            config.channel_id = detail.value.trim();
                            this.setState({config: config});
                            this.resetConfigValidation();
                        }}                         
                        value={this.state.config !== undefined && this.state.config !==null?this.state.config.channel_id:1} 
                        invalid={this.state.invalidConfig.invalidChannelId}
                        />:
                      <label>{this.channel_id}</label>}
                      <br/>
                      <label>{this.channel_name}</label>
                    </FormField>
                    </ColumnLayout>
                  }
                  
                </Container>
                <br/>
                <ExpandableSection variant='container'
                  expanded={this.state.imageExpanded} 
                  onChange={e=> this.setState({imageExpanded:!this.state.imageExpanded})}
                  headerText="Image Moderation Rules"
                  >
                <ColumnLayout columns={2}>
                  <FormField
                      label="Moderation frequency (in second)"
                      description="How frequent Rules Engine sample images from video stream. Ex, 60 means moderate every 60 seconds."
                      stretch={true}
                    >
                      <Input inputMode="decimal"
                        onChange={({ detail }) => {
                          var f = detail.value.length === 0? "": parseFloat(detail.value);
                          if (detail.value.length > 0 && isNaN(f)) {
                            return;
                          }
                        
                          let config = this.state.config;
                          config.image.sample_frequency_s = f;
                          this.setState({config: config});
                          this.resetConfigValidation();
                        }} 
                        width="100px"
                        value={this.state.config !== undefined && this.state.config !== null?this.state.config.image.sample_frequency_s:60} 
                        invalid={this.state.invalidConfig.invalidImageFreqency}
                      />
                    </FormField>
                    <FormField
                      label="Enable similiarity check"
                      description="When activated, the Rules Engine compares incoming images with the previous channel thumbnail."
                      stretch={true}
                    >
                      <Checkbox 
                        onChange={({ detail }) => {
                            let config = this.state.config;
                            config.image.ignore_similar = detail.checked;
                            this.setState({config: config});
                            this.resetConfigValidation();
                        }} 
                        checked={this.state.config !== undefined && this.state.config !== null?this.state.config.image.ignore_similar:true} 
                      />
                    </FormField>
                    {/* <FormField
                      label="Similarity comparison threshold"
                      description="The hash delta threshold for similiarity comparison"
                      stretch={true}
                    >
                      <Input 
                        onChange={({ detail }) => {
                          var f = detail.value.length === 0? "": parseFloat(detail.value);
                          if (detail.value.length > 0 && isNaN(f)) {
                            return;
                          }
                        
                          let config = this.state.config;
                          if (config !== undefined && config !== null) {
                            config.image.image_hash_threshold = f;
                            this.setState({config: config});
                            this.resetConfigValidation();
                          }
                        }} 
                        disabled={this.state.config !== undefined && this.state.config !== null?!this.state.config.image.ignore_similar:false}
                        value={this.state.config !== undefined && this.state.config !== null?this.state.config.image.image_hash_threshold:10} 
                        invalid={this.state.invalidConfig.invalidSimilarThreshold}
                      />
                    </FormField> */}
                  </ColumnLayout>
                    <Modal
                        onDismiss={() => {this.setState({showEditRuleModal: false}); }}
                        visible={this.state.showEditRuleModal}
                        header={this.state.selectedImageRules === null || this.state.selectedImageRules.length === 0? "Add Rule": "Edit Rule"}
                        size="large"
                        >
                          <div className="editrule">
                          {this.state.ruleAlert !== null?
                              <div className="alert">
                              <Alert dismissible 
                                onDismiss={e => this.setState({ruleAlert: null})}
                                statusIconAriaLabel="Alert"
                              >
                                {this.state.ruleAlert}
                              </Alert></div>:<div/>
                            }
                            <ColumnLayout columns={2}>
                                <FormField
                                    label="Rule Name"
                                    description="A name to describe the rule. For example, Nudity with 70% threshold"
                                    stretch={true}
                                >
                                <Input autoFocus
                                    onChange={e=> {
                                        this.setState({currentRuleName: e.detail.value});
                                    }}                      
                                    value={this.state.currentRuleName !== null ?this.state.currentRuleName:""} 
                                    invalid={this.state.invalidConfigName}
                                    />
                                </FormField>
                                <FormField
                                    label="Auto termination"
                                    description="Automatically terminate the IVS live stream"
                                    stretch={true}
                                >
                                  <Checkbox onChange={
                                      ({detail}) => {
                                        this.setState({currentRuleAutoStop: detail.checked});
                                      }
                                    }
                                    checked={this.state.currentRuleAutoStop}
                                    ></Checkbox>
                                </FormField> 
                              </ColumnLayout>
                              <ColumnLayout columns={2}>                            
                                <FormField
                                    label="Moderation Categories"
                                    description="If you leave the sub-category empty, the rule will apply to all categories under the top category."
                                    stretch={true}
                                >
                                {/* <DropdownTreeSelect data={this.state.moderationCategories} className='mdl-demo' onChange={this.handelDropdownTreeSelect} /> */}
                                <TokenGroup 
                                  onDismiss={({ detail: { itemIndex } }) => {
                                    console.log(this.state.currentCategories);
                                    let cats = this.state.currentCategories;
                                    cats.splice(itemIndex, 1);
                                    this.setState({currentCategories: cats});
                                  }}
                                  items={this.state.currentCategories !== null ?this.state.currentCategories.map(str => ({ label: str })):[]}
                                ></TokenGroup>
                                <Autosuggest onSelect={({detail}) => {
                                  console.log(detail);
                                    if (!this.state.currentCategories.includes(detail.value)) {
                                      let cats = this.state.currentCategories;
                                      cats.push(detail.value);
                                      this.setState({currentCategories: cats});
                                    }
                                  }}
                                  options={this.state.moderationCategories}
                                  value={this.state.currentSearchCategoryText}
                                  onChange={({detail}) => this.setState({currentSearchCategoryText: detail.value})}
                                  empty="Select a moderation category"
                                >
                                </Autosuggest>
                                {this.state.invalidRuleCategories?<div className='invalid'>Please choose moderation categories</div>:<div/>}
                                </FormField>
                                <FormField
                                    label="Confidence Threshold"
                                    description="Between 0 and 100%"
                                    stretch={true}
                                >
                                <Slider
                                    aria-label="Custom marks"
                                    value={this.state.currentRuleConfidence !== null? this.state.currentRuleConfidence: 60}
                                    valueLabelDisplay="auto"
                                    className="slider"
                                    step={5}
                                    marks={[
                                        {
                                          value: 0,
                                          label: '0%',
                                        },
                                        {
                                          value: 20,
                                          label: '20%',
                                        },
                                        {
                                            value: 40,
                                            label: '40%',
                                        },
                                        {
                                          value: 60,
                                          label: '60%',
                                        },
                                        {
                                            value: 80,
                                            label: '80%',
                                        },                                
                                        {
                                          value: 100,
                                          label: '100%',
                                        },
                                      ]}
                                    getAriaValueText={value => `${value}%`}
                                    min={0}
                                    max={100}
                                    size="large"
                                    onChange={e=> {
                                        this.setState({currentRuleConfidence: e.target.value});
                                    }}           
                                    />
                                </FormField>   
                            </ColumnLayout>
                            <div className='rulebuttoncontainer'>
                            <Button variant='primary' onClick={this.handleSaveImageRule}>Save</Button>
                            <Button onClick={e=> {this.setState({showEditRuleModal: false, invalidConfigName: false, invalidRuleCategories: false})}}>Cancel</Button>
                            </div>
                          </div>
                    </Modal>
                    {this.state.invalidConfig.invalidImageRules? <div className="invalid">Please ensure to define at least one image rule.</div>:<div/>}
                  <div className="rule-title">Image rules</div>
                  <div className="rule-add">
                  <Button onClick={e=> {
                    this.setState({
                      selectedImageRules:[this.constructImageRule()], 
                      showEditRuleModal: true,
                      currentRuleName: "",
                      currentCategories: [],
                      currentRuleConfidence: 60,
                      currentRuleAutoStop: true
                    });
                    this.resetConfigValidation();
                  }}>Add rule</Button>
                  </div>
                  {this.state.config !== null && this.state.config.image.rules !== undefined && this.state.config.image.rules !== null?
                    <div className='rules'>
                      <div className='rule-row'>
                        <div className='header-cell'>Name</div>
                        <div className='header-cell'>Categories</div>
                        <div className='header-cell'>Confidence Threshold</div>
                        <div className='header-cell'>Auto Stop</div>
                        <div className='header-cell'>Actions</div>
                      </div>
                     {this.state.config.image.rules.map((rule) => (
                      <div className='rule-row'>
                        <div className='rule-cell'>{rule.name}</div>
                        <div className='rule-cell'>{rule.categories.join(", ")}</div>
                        <div className='rule-cell'>{rule.confidence_threshold}</div>
                        <div className='rule-cell'>{rule.auto_stop === undefined || rule.auto_stop === null || !rule.auto_stop? "No": "Yes"}</div>
                        <div className='rule-cell'>
                          <Button variant='icon' iconName='edit' onClick={
                            e=>{
                              this.setState({
                                selectedImageRules: [rule], 
                                showEditRuleModal: true,
                                currentRuleName: rule.name,
                                currentCategories: rule.categories,
                                currentRuleConfidence: rule.confidence_threshold,
                                currentRuleAutoStop: rule.auto_stop === undefined || rule.auto_stop === null || !rule.auto_stop?false:true
                              })
                            }}></Button>
                          <Button variant='icon' iconName='delete-marker' onClick={
                            (e)=>{
                              console.log(e,rule);
                              let config = this.state.config;
                              const updatedRules = config.image.rules.filter(r => r.id !== rule.id);
                              config.image.rules = updatedRules;
                              this.setState({selectedImageRules: [], config: config})
                            }}></Button>
                        </div>
                      </div>
                    ))}
                    </div>
                  :<div/>}
                  
                    
                </ExpandableSection>
                <div className='buttoncontainer'>
                <Button variant='primary' loading={this.state.status === "loading"} onClick={this.handleSumbit}>Save Config</Button>
                <Button onClick={this.handelCancel}>Cancel</Button>
                </div>
            </div>
        );
    }
}

export default ConfigDetail;