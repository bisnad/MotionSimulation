#include "ofApp.h"
#include "dab_flock_parameter.h"
#include "dab_flock_euler_integration.h"
#include "dab_flock_agent.h"
#include "dab_flock_swarm.h"
#include "dab_flock_simulation.h"
#include "dab_flock_com.h"
#include "dab_flock_osc_control.h"
#include "dab_space_includes.h"
#include "dab_flock_behavior_includes.h"
#include "dab_flock_visual.h"
#include "dab_flock_com.h"
#include "dab_com_mocap_swarm_listener.h"
#include "dab_math_roesseler_field_algorithm.h"
#include "dab_geom_line.h"
#include "ofTrueTypeFont.h"
#include "dab_flock_text_tools.h"
#include "dab_flock_serialize.h"
using namespace dab;
using namespace dab::flock;

//--------------------------------------------------------------
void ofApp::setup()
{
	SerializeTools& serializeTools = SerializeTools::get();

	try
	{
		Simulation& simulation = Simulation::get();
		simulation.setUpdateInterval(1.0);

		simulation.com().createOscControl(7400, "127.0.0.1", 7800);
		simulation.com().createSender("FlockSender", "127.0.0.1", 7500, false);
		//simulation.com().createSender("FlockSender_Pablo", "2.0.0.31", 9005, false);
		simulation.com().createSender("FlockSender_Pablo", "192.168.0.162", 9005, false);
		//simulation.com().createSender("FlockSender", "127.0.0.1", 7500, true);

		// setup mocap joint position space
		simulation.space().addSpace(std::shared_ptr<space::Space>(new space::Space("mocap_position", new space::KDTreeAlg(3))));

		// create mocap swarm
		Swarm* mocap_warm = new Swarm("mocap_swarm");
		mocap_warm->addParameter("position", { 0.0, 0.0, 0.0 });
		mocap_warm->assignNeighbors("position", "mocap_position", false, NULL);
		mocap_warm->addParameter("velocity", { 0.1, 0.0, 0.0 });

		int mocapJointCount = 23; // Xsens: 23, Qualisys: 64
		int mocapRightHandJointIndex = 11; // right hand joint index, Xsens: 11, Qualisys: 35

		mocap_warm->addAgents(mocapJointCount);

		// debug begin
		// change parameter visibility
		int visibleJointIndex = mocapRightHandJointIndex;
		std::vector<dab::flock::Agent*>& mocapAgents = mocap_warm->agents();
		for (int agentI = 0; agentI < mocapJointCount; ++agentI)
		{
			if(agentI != visibleJointIndex) mocapAgents[agentI]->assignNeighbors("position", "mocap_position", false);
		}

		// debug end

		// create mocap receiver
		simulation.com().createReceiver("mocap_receiver", 9002); // Xsens: 9005, Qualisys: 9004
		mMocapSwarmListener = std::shared_ptr<dab::com::MocapSwarmListener>( new dab::com::MocapSwarmListener("mocap_swarm") );
		simulation.com().registerListener("mocap_receiver", mMocapSwarmListener);

		// TODO: create a listener class that receives mocap data and applies it to mocap_swarm
		//simulation.com().registerListener()

		// create agent space
		simulation.space().addSpace(std::shared_ptr<space::Space>(new space::Space("agent_position", new space::KDTreeAlg(3))));


		Swarm* swarm = new Swarm("swarm");
		swarm->addParameter("position", { 0.0, 0.0, 0.0 });
		swarm->assignNeighbors("position", "agent_position", true, new space::NeighborGroupAlg(3.0, 8, true));
		swarm->assignNeighbors("position", "mocap_position", false, new space::NeighborGroupAlg(60.0, 1, true));
		swarm->addParameter("velocity", { 0.0, 0.0, 0.0 });
		swarm->addParameter("acceleration", { 0.0, 0.0, 0.0 });
		swarm->addParameter("force", { 0.0, 0.0, 0.0 });
		swarm->addParameter("mass", { 0.1f });

		swarm->addBehavior("resetForce", ResetBehavior("", "force"));

		swarm->addBehavior("randomize", RandomizeBehavior("", "force"));
		swarm->set("randomize_range", { 0.0001f, 0.0001f, 0.0001f });

		swarm->addBehavior("damping", DampingBehavior("velocity", "force"));
		swarm->set("damping_prefVelocity", { 0.5 });
		swarm->set("damping_amount", { 0.1f });

		swarm->addBehavior("targetPos", TargetParameterBehavior("position", "force"));
		swarm->set("targetPos_target", { 0.0, 0.0, 0.0 });
		swarm->set("targetPos_adapt", { 1.0, 1.0, 1.0 });
		swarm->set("targetPos_amount", 0.0); // 0.52 // 0.0
		swarm->set("targetPos_absolute", 0.0);

		swarm->addBehavior("lightPos", TargetParameterBehavior("position", "force"));
		swarm->set("lightPos_target", { 0.0, 0.0, 0.0 });
		swarm->set("lightPos_adapt", { 1.0, 1.0, 1.0 });
		swarm->set("lightPos_amount", 0.0); // 0.52 // 0.0
		swarm->set("lightPos_absolute", 0.0);

		swarm->addBehavior("targetVel", TargetParameterBehavior("velocity", "force"));
		swarm->set("targetVel_target", { 1.0, 0.0, 0.0 });
		swarm->set("targetVel_adapt", { 1.0, 1.0, 1.0 });
		swarm->set("targetVel_amount", 0.0); // 0.52 // 0.0
		swarm->set("targetVel_absolute", 0.0);

		swarm->addBehavior("circular", CircularBehavior("position velocity", "force"));
		swarm->set("circular_centerPosition", { 0.0, 0.0, 0.0 });
		swarm->set("circular_innerRadius", 2.0);
		swarm->set("circular_outerRadius", 2.0);
		swarm->set("circular_ortAmount", 0.0);
		swarm->set("circular_tanAmount", 0.0);

		//swarm->addBehavior("shapeFollow", LineFollowBehavior("position@shapespace", "force"));
		//swarm->set("shapeFollow_minDist", 0.0);
		//swarm->set("shapeFollow_maxDist", 60.0);
		//swarm->set("shapeFollow_contourMaintainDist", 5.0);
		//swarm->set("shapeFollow_tanAmount", 0.02);
		//swarm->set("shapeFollow_ortAmount", 2.0);
		//swarm->set("shapeFollow_amount", 1.0);

		//swarm->addBehavior( "textFollow", LineFollowBehavior("position@textspace","force"));
		//swarm->set("textFollow_minDist", 0.0);
		//swarm->set("textFollow_maxDist", 60.0);
		//swarm->set("textFollow_contourMaintainDist", 5.0);
		//swarm->set("textFollow_tanAmount", 0.02);
		//swarm->set("textFollow_ortAmount", 2.0);
		//swarm->set("textFollow_amount", 1.0);

		//swarm->addBehavior( "forcegrid", GridAvgBehavior( "position@forcegrid", "force" ) );
		//swarm->set("forcegrid_amount", { 0.01 } );

		swarm->addBehavior("cohesion", CohesionBehavior("position@agent_position", "force"));
		swarm->set("cohesion_minDist", { 0.0 });
		swarm->set("cohesion_maxDist", { 3.0 });
		swarm->set("cohesion_amount", { 0.0f });

		swarm->addBehavior("alignment", AlignmentBehavior("position@agent_position:velocity", "force"));
		swarm->set("alignment_minDist", { 0.0 });
		swarm->set("alignment_maxDist", { 3.0 });
		swarm->set("alignment_amount", { 0.0f });

		swarm->addBehavior("evasion", EvasionBehavior("position@agent_position", "force"));
		swarm->set("evasion_maxDist", { 0.2f });
		swarm->set("evasion_amount", { 0.0f });

		swarm->addBehavior("mocap_cohesion", CohesionBehavior("position@mocap_position", "force"));
		swarm->set("mocap_cohesion_minDist", { 0.0 });
		swarm->set("mocap_cohesion_maxDist", { 60.0 });
		swarm->set("mocap_cohesion_amount", { 0.1f });

		swarm->addBehavior("mocap_alignment", AlignmentBehavior("position@mocap_position:velocity", "force"));
		swarm->set("mocap_alignment_minDist", { 0.0 });
		swarm->set("mocap_alignment_maxDist", { 3.0 });
		swarm->set("mocap_alignment_amount", { 0.0f });

		swarm->addBehavior("mocap_evasion", EvasionBehavior("position@mocap_position", "force"));
		swarm->set("mocap_evasion_maxDist", { 0.2f });
		swarm->set("mocap_evasion_amount", { 0.0f });

		swarm->addBehavior("boundaryWrap", BoundaryWrapBehavior("position", "position"));
		swarm->set("boundaryWrap_lowerBoundary", { -5.0, -5.0, -5.0 });
		swarm->set("boundaryWrap_upperBoundary", { 5.0, 5.0, 5.0 });

		//      swarm->addBehavior( "boundaryRepulsion", BoundaryRepulsionBehavior( "position", "force" ) );
		//		swarm->set( "boundaryRepulsion_lowerBoundary", { -5.0, -5.0, -5.0 } );
		//		swarm->set( "boundaryRepulsion_upperBoundary", { 5.0, 5.0, 5.0 } );
		//		swarm->set( "boundaryRepulsion_maxDist", { 2.5 } );
		//		swarm->set( "boundaryRepulsion_amount", { 0.13 } );

		swarm->addBehavior("boundaryMirror", BoundaryMirrorBehavior("position velocity force", "velocity force"));
		swarm->set("boundaryMirror_lowerBoundary", { -5.0, -5.0, -5.0 });
		swarm->set("boundaryMirror_upperBoundary", { 5.0, 5.0, 5.0 });
		swarm->set("boundaryMirror_active", 0.0);

		swarm->addBehavior("acceleration", AccelerationBehavior("mass velocity force", "acceleration"));
		swarm->set("acceleration_maxAngularAcceleration", { 1.0, 1.0, 1.0 });

		swarm->addBehavior("integration", EulerIntegration("position velocity acceleration", "position velocity"));
		swarm->set("integration_timestep", { 0.1f });

		//swarm->addBehavior( "print", ParameterPrintBehavior("position", "") );

		swarm->addAgents(16);
		swarm->randomize("position", { -1.0, -1.0, -1.0 }, { 1.0, 1.0, 1.0 });

		// set light positions
		float light_ground_z = 0.0;
		float light_ceil_z = 5.0;
		int light_per_ring_count = 8;
		float ring_radius = 2.5;
		float ring_angle_increment = (PI * 2.0) / static_cast<float>(light_per_ring_count);
		float ring_angle_start = -PI / 2.0 - PI / 8.0; // slight offset of first light

		for (int i = 0; i < light_per_ring_count; ++i)
		{
			float ring_angle = ring_angle_start + static_cast<float>(i) * ring_angle_increment;

			float posX = ring_radius * cos(ring_angle);
			float posY = ring_radius * sin(ring_angle);

			swarm->agent(i)->parameter("lightPos_target")->setValues({ posX , posY , light_ground_z });
			swarm->agent(i + light_per_ring_count)->parameter("lightPos_target")->setValues({ posX , posY , light_ceil_z });
		}

		//std::cout << "swarm\n" << swarm->info(2) << "\n";

		//simulation.com().registerParameter("FlockSender", "swarm", "position" );
		//simulation.com().registerParameter("FlockSender", "swarm", "position", Eigen::Vector3f(-5.0, -5.0, -5.0), Eigen::Vector3f(5.0, 5.0, 5.0) );
		//simulation.com().registerParameter("FlockSender", "swarm", "position", std::array<int, 2>( { 5, 10 } ) );
		simulation.com().registerParameter("FlockSender", "swarm", "position", swarm->agentCount());
		simulation.com().registerParameter("FlockSender", "swarm", "velocity", swarm->agentCount());
		//simulation.com().registerParameter("FlockSender", "swarm", "position", swarm->agentCount(), Eigen::Vector3f(-5.0, -5.0, -5.0), Eigen::Vector3f(5.0, 5.0, 5.0));
		//simulation.com().registerParameter("FlockSender", "swarm", "velocity", swarm->agentCount());

		simulation.com().registerParameter("FlockSender_Pablo", "swarm", "position", swarm->agentCount());
		simulation.com().registerParameter("FlockSender_Pablo", "swarm", "velocity", swarm->agentCount());

		FlockVisuals& visuals = FlockVisuals::get();
		visuals.showSwarm("swarm", "position", "velocity", 10);
		visuals.showSwarm("mocap_swarm", "position", "velocity", 10);

		visuals.setAgentColor("mocap_swarm", {1.0, 0.0, 0.0, 1.0});
		visuals.setTrailColor("mocap_swarm", { 1.0, 0.0, 0.0, 1.0 });

		//visuals.showSwarm("swarm", "position", "");
		visuals.setAgentScale("swarm", 0.05);
		visuals.setAgentScale("mocap_swarm", 0.05);
		//        visuals.showSpace("agent_position");
		//        visuals.showSpace("agent_position");
		//        visuals.showSpace("forcegrid");
		//        visuals.setSpaceColor("forcegrid", std::array<float,4>( { 0.0, 0.0, 0.0, 0.2 } ));
		//        visuals.setSpaceValueScale("forcegrid", 0.1);

		visuals.setDisplayPosition(ofVec3f(0, -1.8, -22.1));
		visuals.setDisplayZoom(0.2);
		visuals.setDisplayOrientation(ofQuaternion(0.5, -0.5, -0.5, -0.5));

		simulation.start();
		simulation.setUpdateInterval(20.0);
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}

	ofSetFrameRate(60);
}

//--------------------------------------------------------------
void ofApp::update()
{
	//std::cout << "ofApp::update() begin\n";

	mMocapSwarmListener->update();

	//Simulation::get().update();
	FlockVisuals::get().update();

	//std::cout << "ofApp::update() end\n";
}

//--------------------------------------------------------------
void ofApp::draw()
{
	//std::cout << "ofApp::draw() begin\n";

	//FlockVisuals::get().update();
	FlockVisuals::get().display();

	//std::cout << "ofApp::draw() end\n";
}

//--------------------------------------------------------------
void ofApp::keyPressed(int key)
{
	if (key == 'f')
	{
		ofGetMainLoop()->getCurrentWindow()->toggleFullscreen();
		//ofGetMainLoop()->getCurrentWindow()->setWindowShape(windowSize[0], windowSize[1]);
		//ofGetMainLoop()->getCurrentWindow()->setWindowPosition(windowPos[0], windowPos[1]);
	}
}

//--------------------------------------------------------------
void ofApp::keyReleased(int key) {

}

//--------------------------------------------------------------
void ofApp::mouseMoved(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::mouseDragged(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mousePressed(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mouseReleased(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mouseEntered(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::mouseExited(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::windowResized(int w, int h) {

}

//--------------------------------------------------------------
void ofApp::gotMessage(ofMessage msg) {

}

//--------------------------------------------------------------
void ofApp::dragEvent(ofDragInfo dragInfo) {

}

