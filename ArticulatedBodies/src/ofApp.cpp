#include "ofApp.h"
#include "ofVectorMath.h"
#include "ofxAssimpModelLoader.h"
#include "dab_value.h"
#include "dab_physics_state.h"
#include "dab_geom_mesh_manager.h"
#include "dab_physics_simulation.h"
#include "dab_physics_body_shape.h"
#include "dab_physics_body_part.h"
#include "dab_physics_universal_joint.h"
#include "dab_physics_universal_motor.h"
#include "dab_physics_body.h"
#include "dab_physics_behavior_force.h"
#include "dab_physics_behavior_random_force.h"
#include "dab_physics_behavior_rotation_target.h"
#include "dab_physics_behavior_rotation_target_oscil.h"
#include "dab_physics_behavior_random_rotation_target.h"
#include "dab_physics_behavior_target_attraction.h"
#include "dab_physics_behavior_volume.h"
#include "dab_physics_behavior_speed.h"
#include "dab_physics_neighbor_behavior_cohesion.h"
#include "dab_physics_neighbor_behavior_alignment.h"
#include "dab_vis_body_visualization.h"
#include "dab_vis_camera.h"
#include "dab_com_osc_control.h"
#include "dab_urdf_importer.h"
#include <btBulletDynamicsCommon.h>
#include "dab_value.h"
#include "dab_string_tools.h"
#include "dab_physics_state_serialize.h"

//--------------------------------------------------------------

void
ofApp::setup()
{
	//dab::StringTools& stringTools = dab::StringTools::get();

	//std::string searchString = "today is nice weather";
	//std::string wildcardString = "today*nice*";

	//std::vector<std::string> matchingStrings = stringTools.wildCardMatch(wildcardString, { searchString });

	//std::cout << "matchingStrings: ";
	//for (int sI = 0; sI < matchingStrings.size(); ++sI) std::cout << matchingStrings[sI] << " / ";
	//std::cout << "\n";


	try
	{
		dab::UrdfImporter& urdfImporter = dab::UrdfImporter::get();
		//urdfImporter.loadURDF(ofToDataPath("3d_models/testblock3/body.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/quadruped/body.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/tubes_v1/body.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/cubes/body.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/tubes_v2/body.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/bullet_examples/capsule.urdf"));

		//urdfImporter.loadURDF(ofToDataPath("3d_models/cubes_v2/robot.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/links_v3/robot.urdf"));

		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v1/robot.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v2/robot.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v3/robot.urdf"));
		urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v3_v2/robot.urdf")); // standard simple arm
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v4/robot.urdf"));
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v5/robot.urdf")); // more segments in one arm
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v5_v2/robot.urdf")); // even more segments in one arm (17 joints to be precise)
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_links_v6/robot.urdf")); // crazy many segments in one arm
		//urdfImporter.loadURDF(ofToDataPath("3d_models/base_multilinks_v1/robot.urdf")); // a body with branching arms
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}


	////preload meshes
	//dab::geom::MeshManager& meshManager = dab::geom::MeshManager::get();

	//try
	//{
	//	std::string meshName = "";

	//	meshManager.loadMesh(meshName, ofToDataPath("3d_models/quadruped/upperlimb.stl"), 0);
	//
	//	std::cout << "meshName " << meshName << "\n";
	//}
	//catch (dab::Exception& e)
	//{
	//	std::cout << e << "\n";
	//}

	setupPhysics();
	//setupStates();
	setupGraphics();
	setupOsc();

	//mGui.setup();

	dab::physics::Simulation::get().start();
	//mStateMachine->start();

	ofBackground(0, 0, 0);
	ofSetFrameRate(60);
	ofSetVerticalSync(true);
}

void
ofApp::setupPhysics()
{
	dab::physics::Simulation& physics = dab::physics::Simulation::get();
	physics.setTimeStep(0.1);
	physics.setSupSteps(20);
	physics.setGravity(glm::vec3(0.0, 0.0, 0.0));

	try
	{
		//// create ground shape and object
		//std::shared_ptr<dab::physics::BodyBoxShape> groundShape = physics.addBoxShape("GroundShape", glm::vec3(20.0, 20.0, 1.0));
		//std::shared_ptr<dab::physics::Body> groundBody = physics.addBody("ground");
		//std::shared_ptr< dab::physics::BodyPart> groundObject = physics.addBodyPart("ground", "ground", "GroundShape", true, 0.0);
		//groundObject->setPosition(glm::vec3(0.0, 0.0, 6.0));
		////groundObject->setResitution(0.0);
		////groundObject->setFriction(0.1);
		////groundObject->setLinearDamping(0.3);

		//// rotate and position base object
		//std::shared_ptr<dab::physics::Body> body = physics.body("onshape");
		//std::shared_ptr<dab::physics::BodyPart> base = physics.part("onshape", "base");
		//glm::quat baseRot = glm::quat(glm::vec3(PI / 2.0, 0.0, 0.0));
		//base->setRotation(baseRot);
		//glm::vec3 pos(0.0, 0.92, 0.45);
		//base->setPosition(pos);

		//// debug begin: setup physics behaviour

		//std::vector<std::string> partNames = { "part_1", "link_v2", "part_1_2", "link_v2_2" };
		//std::vector<std::string> motorNames = { "joint1", "joint2", "joint3", "joint4" };
		////std::vector<std::string> motorNames = { "joint1" };

		const std::vector<std::shared_ptr<dab::physics::BodyPart>>& bodyParts = physics.body("onshape")->parts();
		const std::vector<std::shared_ptr<dab::physics::BodyJoint>>& bodyJoints = physics.body("onshape")->joints();

		std::vector<std::string> partNames = {};
		for (auto bodyPart : bodyParts) partNames.push_back(bodyPart->name());

		std::vector<std::string> jointNames = {};
		for (auto bodyJoint : bodyJoints) jointNames.push_back(bodyJoint->name());

		// debug begin
		for (int pI = 0; pI < partNames.size(); ++pI) std::cout << "part : " << pI << " name : " << partNames[pI] << "\n";
		for (int jI = 0; jI < jointNames.size(); ++jI) std::cout << "joint : " << jI << " name : " << jointNames[jI] << "\n";
		// debug end

		// ´basic behaviors

		std::shared_ptr<dab::physics::RandomForceBehavior> randomTipBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::RandomForceBehavior>("onshape", "random_tip", { partNames[partNames.size() - 1] }, {}, {});
		randomTipBehaviour->set("active", false);
		randomTipBehaviour->set("minDir", { -1.0f, -1.0f, -1.0f });
		randomTipBehaviour->set("maxDir", { 1.0f, 1.0f, 1.0f });
		randomTipBehaviour->set("minAmp", 1.0f);
		randomTipBehaviour->set("maxAmp", 1.0f);
		randomTipBehaviour->set("appInterval", 1.0f);
		randomTipBehaviour->set("randInterval", 5000.0f);

		std::shared_ptr<dab::physics::RandomForceBehavior> randomAllBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::RandomForceBehavior>("onshape", "random_all", partNames, {}, {});
		randomAllBehaviour->set("active", false);
		randomAllBehaviour->set("minDir", { -1.0f, -1.0f, -1.0f });
		randomAllBehaviour->set("maxDir", { 1.0f, 1.0f, 1.0f });
		randomAllBehaviour->set("minAmp", 1.0f);
		randomAllBehaviour->set("maxAmp", 1.0f);
		randomAllBehaviour->set("appInterval", 1.0f);
		randomAllBehaviour->set("randInterval", 5000.0f);

		std::shared_ptr<dab::physics::ForceBehavior> forceTipBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::ForceBehavior>("onshape", "force_tip", { partNames[partNames.size() - 1] }, {}, {});
		forceTipBehaviour->set("active", false);
		forceTipBehaviour->set("dir", { 1.0f, 0.0f, 0.0f });
		forceTipBehaviour->set("amp", 1.0f);
		forceTipBehaviour->set("appInterval", 1.0f);

		for (int jI = 0; jI < jointNames.size(); ++jI)
		{
			std::shared_ptr<dab::physics::RotationTargetBehavior> rotationTargetBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RotationTargetBehavior>("onshape", "rotation_" + std::to_string(jI), {}, {}, { jointNames[jI] });
			rotationTargetBehavior->set("active", false);
			rotationTargetBehavior->set("target", { 0.0f, 0.0f, 0.0f });
			rotationTargetBehavior->set("speed", 1.4f);
			rotationTargetBehavior->set("appInterval", 1.0f);
		}

		for (int jI = 0; jI < jointNames.size(); ++jI)
		{
			std::shared_ptr<dab::physics::RotationTargetOscilBehavior> rotationTargetOscilBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RotationTargetOscilBehavior>("onshape", "rotation_oscil_" + std::to_string(jI), {}, {}, { jointNames[jI] });
			rotationTargetOscilBehavior->set("active", false);
			rotationTargetOscilBehavior->set("target1", { 0.0f, 0.0f, -1.0f });
			rotationTargetOscilBehavior->set("target2", { 0.0f, 0.0f, 1.0f });
			rotationTargetOscilBehavior->set("speed", 1.4f);
			rotationTargetOscilBehavior->set("oscilInterval", 1000.0f);
			rotationTargetOscilBehavior->set("appInterval", 1.0f);
		}

		std::shared_ptr<dab::physics::SpeedBehavior> speedTipBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::SpeedBehavior>("onshape", "speed_tip", { partNames[partNames.size() - 1] }, {}, {});
		speedTipBehavior->set("active", false);
		speedTipBehavior->set("speed", 1.0f);
		speedTipBehavior->set("amount", 1.0f);

		std::shared_ptr<dab::physics::SpeedBehavior> speedAllBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::SpeedBehavior>("onshape", "speed_all", partNames, {}, {});
		speedAllBehavior->set("active", false);
		speedAllBehavior->set("speed", 1.0f);
		speedAllBehavior->set("amount", 1.0f);

		// interaction behaviors

		std::shared_ptr<dab::physics::TargetAttractionBehavior> targetAttractionTipBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::TargetAttractionBehavior>("onshape", "targetpos_tip", { partNames[partNames.size() - 1] }, {}, {});
		targetAttractionTipBehaviour->set("active", false);
		targetAttractionTipBehaviour->set("targetPos", { 0.0f, 2.0f, 0.0f });
		targetAttractionTipBehaviour->set("maxDist", 10.0f);
		targetAttractionTipBehaviour->set("minAmp", 0.0f);
		targetAttractionTipBehaviour->set("maxAmp", 1.0f);
		targetAttractionTipBehaviour->set("appInterval", 1.0f);

		std::shared_ptr<dab::physics::TargetAttractionBehavior> targetAttractionAllBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::TargetAttractionBehavior>("onshape", "targetpos_all", partNames, {}, {});
		targetAttractionAllBehaviour->set("active", false);
		targetAttractionAllBehaviour->set("targetPos", { 0.0f, 2.0f, 0.0f });
		targetAttractionAllBehaviour->set("maxDist", 10.0f);
		targetAttractionAllBehaviour->set("minAmp", 0.0f);
		targetAttractionAllBehaviour->set("maxAmp", 1.0f);
		targetAttractionAllBehaviour->set("appInterval", 1.0f);

		// movement quality behaviors
		std::shared_ptr<dab::physics::RandomForceBehavior> levitationBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::RandomForceBehavior>("onshape", "levitation", { partNames[partNames.size() - 1] }, {}, {});
		levitationBehaviour->set("active", false);
		levitationBehaviour->set("minDir", { -1.0f, -1.0f, -1.0f });
		levitationBehaviour->set("maxDir", { 1.0f, 1.0f, 1.0f });
		levitationBehaviour->set("minAmp", 1.0f);
		levitationBehaviour->set("maxAmp", 1.0f);
		levitationBehaviour->set("appInterval", 1.0f);
		levitationBehaviour->set("randInterval", 5000.0f);

		std::shared_ptr<dab::physics::RandomForceBehavior> particlesBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::RandomForceBehavior>("onshape", "particles", { partNames[partNames.size() - 1] }, {}, {});
		particlesBehaviour->set("active", false);
		particlesBehaviour->set("minDir", { -1.0f, -1.0f, -1.0f });
		particlesBehaviour->set("maxDir", { 1.0f, 1.0f, 1.0f });
		particlesBehaviour->set("minAmp", 1.0f);
		particlesBehaviour->set("maxAmp", 1.0f);
		particlesBehaviour->set("appInterval", 1.0f);
		particlesBehaviour->set("randInterval", 5000.0f);

		std::shared_ptr<dab::physics::RandomRotationTargetBehavior> thrustingBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RandomRotationTargetBehavior>("onshape", "thrusting", {}, {}, { jointNames[0], jointNames[1] });
		thrustingBehavior->set("active", false);
		thrustingBehavior->set("minTarget", { 0.0f, 0.0f, -1.4f });
		thrustingBehavior->set("maxTarget", { 0.0f, 0.0f, 1.4f });
		thrustingBehavior->set("speed", 1.4f);
		thrustingBehavior->set("appInterval", 1.0f);
		thrustingBehavior->set("randInterval", 2000.0f);

		std::shared_ptr<dab::physics::RandomRotationTargetBehavior> staccatoBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RandomRotationTargetBehavior>("onshape", "staccato", {}, {}, jointNames);
		staccatoBehavior->set("active", false);
		staccatoBehavior->set("minTarget", { 0.0f, 0.0f, -1.4f });
		staccatoBehavior->set("maxTarget", { 0.0f, 0.0f, 1.4f });
		staccatoBehavior->set("speed", 1.4f);
		staccatoBehavior->set("appInterval", 1.0f);
		staccatoBehavior->set("randInterval", 2000.0f);

		std::shared_ptr<dab::physics::RandomRotationTargetBehavior> fluidityBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RandomRotationTargetBehavior>("onshape", "fluidity", {}, {}, jointNames);
		fluidityBehavior->set("active", false);
		fluidityBehavior->set("minTarget", { 0.0f, 0.0f, -1.4f });
		fluidityBehavior->set("maxTarget", { 0.0f, 0.0f, 1.4f });
		fluidityBehavior->set("speed", 0.1f);
		fluidityBehavior->set("appInterval", 1.0f);
		fluidityBehavior->set("randInterval", 1000.0f);

		//std::shared_ptr<dab::physics::VolumeBehavior> volumeBehaviour = dab::physics::Simulation::get().addBehavior<dab::physics::VolumeBehavior>("onshape", "volume", { "link_v2_2", "part_1" }, {}, {});
		//volumeBehaviour->set("active", false);
		//volumeBehaviour->set("maxDist", 10.0f);
		//volumeBehaviour->set("minAmp", 0.0f);
		//volumeBehaviour->set("maxAmp", 1.0f);
		//volumeBehaviour->set("appInterval", 1.0f);

		//std::shared_ptr<dab::physics::RandomForceBehavior> randomForceBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RandomForceBehavior>("randforce", partNames, {}, {});
		//randomForceBehavior->set("active", false);
		//randomForceBehavior->set("minDir", { -1.0f, -1.0f, -1.0f });
		//randomForceBehavior->set("maxDir", { 1.0f, 1.0f, 1.0f });
		//randomForceBehavior->set("minAmp", 0.1f);
		//randomForceBehavior->set("maxAmp", 0.1f);
		//randomForceBehavior->set("appInterval", 1.0f);
		//randomForceBehavior->set("randInterval", 250.0f);

		//std::shared_ptr<dab::physics::RandomRotationTargetBehavior> randomRotTargetBehavior = dab::physics::Simulation::get().addBehavior<dab::physics::RandomRotationTargetBehavior>("randrottarget", {}, {}, motorNames);
		//randomRotTargetBehavior->set("active", false);
		//randomRotTargetBehavior->set("minTarget", { 0.0f, 0.0f, -1.4f });
		//randomRotTargetBehavior->set("maxTarget", { 0.0f, 0.0f, 1.4f });
		//randomRotTargetBehavior->set("speed", 0.1f);
		//randomRotTargetBehavior->set("appInterval", 1.0f);
		//randomRotTargetBehavior->set("randInterval", 2000.0f);

		//// make copies of body
		//physics.copyBody("onshape", "onshape2");

		/*
		physics.copyBody("onshape", "onshape3");
		physics.copyBody("onshape", "onshape4");
		physics.copyBody("onshape", "onshape5");
		physics.copyBody("onshape", "onshape6");
		physics.copyBody("onshape", "onshape7");
		physics.copyBody("onshape", "onshape8");
		*/

		// linear array of bodies
		std::shared_ptr<dab::physics::BodyPart> base;

		glm::vec3 bodyMinPos(-1.5, 0.0, 0.0);
		glm::vec3 bodyMaxPos(1.5, 0.0, 0.0);
		//glm::quat bodyRot(glm::vec3(-PI / 2.0, 0.0, 0.0));
		glm::quat bodyRot(glm::vec3(PI / 2.0, 0.0, 0.0));
		int bodyCount = 4;

		for (int bI = 0; bI < bodyCount; ++bI)
		{
			glm::vec3 bodyPos = bodyMinPos + (bodyMaxPos - bodyMinPos) * float(bI) / float(bodyCount - 1);

			std::string bodyName = "onshape";

			if (bI > 0)
			{
				bodyName += std::to_string(bI + 1);
				physics.copyBody("onshape", bodyName);
			}


			base = physics.part(bodyName, "base");
			base->setPosition(bodyPos);
			base->setRotation(bodyRot);
		}

		/*
		// left pos & vertical up
		base = physics.part("onshape", "base");
		base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		base->setPosition(glm::vec3(-1.0, 0.0, 0.0));
		
		// right pos & vertical up
		base = physics.part("onshape2", "base");
		base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		base->setPosition(glm::vec3(1.0, 0.0, 0.0));
		*/

		//// center pos & vertical down
		//base = physics.part("onshape", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(0.0, 0.0, 5.0));

		//// center pos & vertical up
		//base = physics.part("onshape", "base");
		//base->setRotation(glm::quat(glm::vec3(PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(0.0, 0.0, 3.0));

		//// center pos & horizontal 
		//base = physics.part("onshape", "base");
		//base->setRotation(glm::quat(glm::vec3(PI / 2.0, PI / 2.0, 0.0)));
		//base->setPosition(glm::vec3(-0.4, 0.0, 4.0));

		//// Grid Arrangement vertical down
		//base = physics.part("onshape", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(-1.0, 1.0, 5.0));

		//base = physics.part("onshape2", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(0.0, 1.0, 5.0));

		//base = physics.part("onshape3", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(1.0, 1.0, 5.0));

		//base = physics.part("onshape4", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(1.0, -1.0, 5.0));

		//base = physics.part("onshape5", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(0.0, -1.0, 5.0));

		//base = physics.part("onshape6", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(-1.0, -1.0, 5.0));

		//base = physics.part("onshape7", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(-1.0, 0.0, 5.0));

		//base = physics.part("onshape8", "base");
		//base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, 0.0)));
		//base->setPosition(glm::vec3(1.0, 0.0, 5.0));

		/*
		// Circle Arrangement vertical up
		{
			int body_offset = 0;
			int body_count = 4;
			float ringPosRadius = 1.5;
			float ringStartPosAngle = -PI / 2.0;
			float ringPosAngleSpacing = PI * 2.0 / (float)body_count;
			float bodyBaseRotation = 0.0;

			for (int bI = body_offset; bI < body_offset + body_count; ++bI)
			{
				std::string bodyName = "onshape";

				if (bI > 0)
				{
					bodyName += std::to_string(bI + 1);
				}

				base = physics.part(bodyName, "base");

				float posAngle = ringStartPosAngle + float(bI) * ringPosAngleSpacing;
				float posX = ringPosRadius * cos(posAngle);
				float posY = ringPosRadius * sin(posAngle);
				bodyBaseRotation = -posAngle;

				base->setPosition(glm::vec3(posX, posY, -0.25));
				base->setRotation(glm::quat(glm::vec3(-PI / 2.0, 0.0, posAngle)));
			}
		}

		// Circle Arrangement vertical down
		{
			int body_offset = 4;
			int body_count = 4;
			float ringPosRadius = 1.5;
			float ringStartPosAngle = -PI / 2.0;
			float ringPosAngleSpacing = PI * 2.0 / (float)body_count;
			float bodyBaseRotation = 0.0;

			for (int bI = body_offset; bI < body_offset + body_count; ++bI)
			{
				std::string bodyName = "onshape";

				if (bI > 0)
				{
					bodyName += std::to_string(bI + 1);
				}

				base = physics.part(bodyName, "base");

				float posAngle = ringStartPosAngle + float(bI) * ringPosAngleSpacing;
				float posX = ringPosRadius * cos(posAngle);
				float posY = ringPosRadius * sin(posAngle);
				bodyBaseRotation = -posAngle;

				base->setPosition(glm::vec3(posX, posY, 0.25));
				base->setRotation(glm::quat(glm::vec3(PI / 2.0, 0.0, posAngle)));
			}
		}
		*/

		// create neighbor behaviors

		//// cohesion
		//std::vector<std::shared_ptr<dab::physics::CohesionBehavior>> cohesionBehaviors = dab::physics::Simulation::get().addNeighborBehavior<dab::physics::CohesionBehavior>({ "onshape","onshape2", "onshape3", "onshape4", "onshape5", "onshape6", "onshape7", "onshape8" }, "cohesion", {"tip_plate"}, { "tip_plate" }, {}, {}, {}, {});
		//for (int bI = 0; bI < cohesionBehaviors.size(); ++bI)
		//{
		//	cohesionBehaviors[bI]->set("active", false);
		//	cohesionBehaviors[bI]->set("minDist", 0.0f);
		//	cohesionBehaviors[bI]->set("maxDist", 10.0f);
		//	cohesionBehaviors[bI]->set("amount", 1.0f);
		//}

		//// evasion
		//std::vector<std::shared_ptr<dab::physics::CohesionBehavior>> evasionBehaviors = dab::physics::Simulation::get().addNeighborBehavior<dab::physics::CohesionBehavior>({ "onshape","onshape2", "onshape3", "onshape4", "onshape5", "onshape6", "onshape7", "onshape8" }, "evasion", { "tip_plate" }, { "tip_plate" }, {}, {}, {}, {});
		//for (int bI = 0; bI < cohesionBehaviors.size(); ++bI)
		//{
		//	evasionBehaviors[bI]->set("active", false);
		//	evasionBehaviors[bI]->set("minDist", 0.0f);
		//	evasionBehaviors[bI]->set("maxDist", 10.0f);
		//	evasionBehaviors[bI]->set("amount", 1.0f);
		//}

		//// alignment
		//std::vector<std::shared_ptr<dab::physics::AlignmentBehavior>> alignmentBehaviors = dab::physics::Simulation::get().addNeighborBehavior<dab::physics::AlignmentBehavior>({ "onshape","onshape2", "onshape3", "onshape4", "onshape5", "onshape6", "onshape7", "onshape8" }, "alignment", { "tip_plate" }, { "tip_plate" }, {}, {}, {}, {});
		//for (int bI = 0; bI < alignmentBehaviors.size(); ++bI)
		//{
		//	alignmentBehaviors[bI]->set("active", false);
		//	alignmentBehaviors[bI]->set("minDist", 0.0f);
		//	alignmentBehaviors[bI]->set("maxDist", 10.0f);
		//	alignmentBehaviors[bI]->set("linearAmount", 1.0f);
		//	alignmentBehaviors[bI]->set("angularAmount", 1.0f);
		//	alignmentBehaviors[bI]->set("amount", 1.0f);
		//}
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void
ofApp::setupStates()
{
	try
	{
		dab::physics::Simulation& physics = dab::physics::Simulation::get();
		dab::physics::StateSerialize& stateSerialize = dab::physics::StateSerialize::get();
		dab::physics::StateManager& stateManager = dab::physics::StateManager::get();
		mStateMachine = std::shared_ptr<dab::physics::StateMachine>(new dab::physics::StateMachine());

		std::vector<std::string> stateBodyParts = { "base", "link_v2", "part_1", "link_v2_2", "part_1_2", "link_v1", "tip_plate" };
		std::vector<std::string> stateBodyMotors = { "joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_top" };
		std::vector<std::string> stateBodies = { "onshape", "onshape2", "onshape3", "onshape4", "onshape5", "onshape6", "onshape7", "onshape8" };
		std::vector<std::string> stateQualityBehaviors = { "fluidity", "levitation", "particles", "staccato", "thrusting" };

		// >> create template states << 

		// create behaviors deactivate state
		std::shared_ptr<dab::physics::State> deactivateState = stateManager.createState("Deactivate");
		deactivateState->addStateEffect(dab::physics::StateEffect(dab::physics::BodyBehaviorEffect, {}, {}, "active", dab::Value<bool>(false)));

		// create thrusting states
		std::shared_ptr<dab::physics::State> thrustingState = stateManager.createState("Thrusting");
		std::shared_ptr<dab::physics::State> thrustingState_physics = stateManager.copyState("Physics", "Thrusting_Physics");
		std::shared_ptr<dab::physics::State> thrustingState_behavior = stateManager.copyState("RandomRotationTargetBehavior", "Thrusting_Behavior");

		stateManager.loadState("Thrusting_Physics", "../controls/physics_control.json", 120, "Physics");
		stateManager.loadState("Thrusting_Behavior", "../controls/thrusting_control.json", 10, "RandomRotationTargetBehavior");

		thrustingState_physics->changeTargets(stateBodyParts, dab::physics::BodyPartEffect);
		thrustingState_physics->changeTargets(stateBodyMotors, dab::physics::BodyMotorEffect);
		thrustingState_behavior->changeTargets({ "thrusting" }, dab::physics::BodyBehaviorEffect);
		thrustingState_behavior->changeParameterValue({ "thrusting" }, "active", dab::Value<bool>(true));

		std::shared_ptr<dab::physics::State> thrustingState_physics2 = stateManager.createState("Thrusting_Physics2");
		thrustingState_physics2->addStateEffect(dab::physics::StateEffect(dab::physics::BodyMotorEffect, {}, {}, "maxAngularMotorForce", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 100.0 })));
		thrustingState_physics2->changeTargets({ "joint_1", "joint_2" }, dab::physics::BodyMotorEffect);

		thrustingState->addSubState(thrustingState_physics);
		thrustingState->addSubState(thrustingState_physics2);
		thrustingState->addSubState(thrustingState_behavior);

		// create staccato states
		std::shared_ptr<dab::physics::State> staccatoState = stateManager.createState("Staccato");
		std::shared_ptr<dab::physics::State> staccatoState_physics = stateManager.copyState("Physics", "Staccato_Physics");
		std::shared_ptr<dab::physics::State> staccatoState_behavior = stateManager.copyState("RandomRotationTargetBehavior", "Staccato_Behavior");

		stateManager.loadState("Staccato_Physics", "../controls/physics_control.json", 130, "Physics");
		stateManager.loadState("Staccato_Behavior", "../controls/staccato_control.json", 10, "RandomRotationTargetBehavior");

		staccatoState_physics->changeTargets(stateBodyParts, dab::physics::BodyPartEffect);
		staccatoState_physics->changeTargets(stateBodyMotors, dab::physics::BodyMotorEffect);
		staccatoState_behavior->changeTargets({ "staccato" }, dab::physics::BodyBehaviorEffect);
		staccatoState_behavior->changeParameterValue({ "staccato" }, "active", dab::Value<bool>(true));

		staccatoState->addSubState(staccatoState_physics);
		staccatoState->addSubState(staccatoState_behavior);

		// create fluidity states
		std::shared_ptr<dab::physics::State> fluidityState = stateManager.createState("Fluidity");
		std::shared_ptr<dab::physics::State> fluidityState_physics = stateManager.copyState("Physics", "Fluidity_Physics");
		std::shared_ptr<dab::physics::State> fluidityState_behavior = stateManager.copyState("RandomRotationTargetBehavior", "Fluidity_Behavior");

		stateManager.loadState("Fluidity_Physics", "../controls/physics_control.json", 140, "Physics");
		stateManager.loadState("Fluidity_Behavior", "../controls/fluidity_control.json", 10, "RandomRotationTargetBehavior");

		fluidityState_physics->changeTargets(stateBodyParts, dab::physics::BodyPartEffect);
		fluidityState_physics->changeTargets(stateBodyMotors, dab::physics::BodyMotorEffect);
		fluidityState_behavior->changeTargets({ "fluidity" }, dab::physics::BodyBehaviorEffect);
		fluidityState_behavior->changeParameterValue({ "fluidity" }, "active", dab::Value<bool>(true));

		fluidityState->addSubState(fluidityState_physics);
		fluidityState->addSubState(fluidityState_behavior);

		// create particles states
		std::shared_ptr<dab::physics::State> particlesState = stateManager.createState("Particles");
		std::shared_ptr<dab::physics::State> particlesState_physics = stateManager.copyState("Physics", "Particles_Physics");
		std::shared_ptr<dab::physics::State> particlesState_behavior = stateManager.copyState("RandomForceBehavior", "Particles_Behavior");

		stateManager.loadState("Particles_Physics", "../controls/physics_control.json", 100, "Physics");
		stateManager.loadState("Particles_Behavior", "../controls/particles_control.json", 10, "RandomForceBehavior");

		particlesState_physics->changeTargets(stateBodyParts, dab::physics::BodyPartEffect);
		particlesState_physics->changeTargets(stateBodyMotors, dab::physics::BodyMotorEffect);
		particlesState_behavior->changeTargets({ "particles" }, dab::physics::BodyBehaviorEffect);
		particlesState_behavior->changeParameterValue({ "particles" }, "active", dab::Value<bool>(true));

		particlesState->addSubState(particlesState_physics);
		particlesState->addSubState(particlesState_behavior);

		// create levitation states
		std::shared_ptr<dab::physics::State> levitationState = stateManager.createState("Levitation");
		std::shared_ptr<dab::physics::State> levitationState_physics = stateManager.copyState("Physics", "Levitation_Physics");
		std::shared_ptr<dab::physics::State> levitationState_behavior = stateManager.copyState("RandomForceBehavior", "Levitation_Behavior");

		stateManager.loadState("Levitation_Physics", "../controls/physics_control.json", 100, "Physics");
		stateManager.loadState("Levitation_Behavior", "../controls/levitation_control.json", 10, "RandomForceBehavior");

		levitationState_physics->changeTargets(stateBodyParts, dab::physics::BodyPartEffect);
		levitationState_physics->changeTargets(stateBodyMotors, dab::physics::BodyMotorEffect);
		levitationState_behavior->changeTargets({ "levitation" }, dab::physics::BodyBehaviorEffect);
		levitationState_behavior->changeParameterValue({ "levitation" }, "active", dab::Value<bool>(true));

		levitationState->addSubState(levitationState_physics);
		levitationState->addSubState(levitationState_behavior);

		// apply one of the states to initialize physics
		std::shared_ptr<dab::physics::State> initState = stateManager.copyState("Fluidity");
		initState->changeBodies(stateBodies, true);
		initState->apply();

		// create meta states

		// create individual states for each body and quality
		// for testing, create staccato state for first body only
		{
			// body0 staccato quality meta state
			std::shared_ptr<dab::physics::State> body0_staccatoState = stateManager.createState("onshape_Staccato");

			// behaviour deactivate state
			std::shared_ptr<dab::physics::State> deactivateState = stateManager.copyState("Deactivate");
			deactivateState->changeTargets(stateQualityBehaviors);
			deactivateState->changeBodies({ "onshape" });
			stateManager.addSubState(body0_staccatoState, deactivateState);

			// TODO: continue
		}



		// create change quality state (for all bodies)
		std::shared_ptr<dab::physics::State> groupQualityState;
		std::shared_ptr<dab::physics::State> travelingFluidityState;
		std::shared_ptr<dab::physics::State> travelingQualityState;

		{
			// create meta state
			std::shared_ptr<dab::physics::State> meta_state = stateManager.createState("GroupQualities");
			std::shared_ptr<dab::physics::State> meta_state_deactivate = stateManager.copyState("Deactivate");

			meta_state_deactivate->changeTargets(stateQualityBehaviors);
			meta_state_deactivate->changeBodies(stateBodies);
			stateManager.addSubState(meta_state, meta_state_deactivate);

			// create states for each quality
			std::vector<std::shared_ptr<dab::physics::State>> qualityStates;
			qualityStates.push_back(stateManager.copyState("Fluidity"));
			qualityStates.push_back(stateManager.copyState("Levitation"));
			qualityStates.push_back(stateManager.copyState("Particles"));
			qualityStates.push_back(stateManager.copyState("Staccato"));
			qualityStates.push_back(stateManager.copyState("Thrusting"));

			int qualityCount = qualityStates.size();
			std::vector<std::shared_ptr<dab::physics::State>> deactivateStates(qualityCount);

			for (int qI = 0; qI < qualityCount; ++qI)
			{
				qualityStates[qI]->changeBodies(stateBodies, true);

				deactivateStates[qI] = stateManager.copyState("Deactivate");

				std::vector<std::string> deactivateQualityNames;
				for (int qI2 = 0; qI2 < qualityCount; ++qI2)
				{
					if (qI2 != qI) deactivateQualityNames.push_back(stateQualityBehaviors[qI2]);
				}
				deactivateStates[qI]->changeBodies(stateBodies);
				deactivateStates[qI]->changeTargets(deactivateQualityNames);

				qualityStates[qI]->addSubState(deactivateStates[qI]);
				deactivateStates[qI]->setParentState(qualityStates[qI]);

				stateManager.addSubState(meta_state, qualityStates[qI]);
			}

			// create state transitions
			dab::physics::StateTransitionTimed stateTransition(10.0);

			for (int qI = 0; qI < qualityCount; ++qI)
			{
				std::shared_ptr<dab::physics::State> startState = qualityStates[qI];
				std::vector<std::shared_ptr<dab::physics::State>> targetStates;

				for (int qI2 = 0; qI2 < qualityCount; ++qI2)
				{
					if (qI2 != qI) targetStates.push_back(qualityStates[qI2]);
				}

				stateManager.createStateTransition(startState, targetStates, stateTransition);
			}

			// set initially active state
			meta_state->setActive(false);
			qualityStates[0]->setActive(true);
			for (int qI = 1; qI < qualityCount; ++qI) qualityStates[qI]->setActive(false);
			//meta_state->apply();

			//mStateMachine->addState(meta_state);

			groupQualityState = meta_state;
		}

		// create single quality traveling from body to body state
		// Fluidity
		{
			// create meta state
			std::shared_ptr<dab::physics::State> meta_state = stateManager.createState("TravelingFluidity");
			std::shared_ptr<dab::physics::State> meta_state_physics = stateManager.copyState("Fluidity_Physics");
			std::shared_ptr<dab::physics::State> meta_state_deactivate = stateManager.copyState("Deactivate");

			//meta_state_physics->changeBodies(stateBodies);
			//stateManager.addSubState(meta_state, meta_state_physics);

			meta_state_deactivate->changeTargets(stateQualityBehaviors);
			meta_state_deactivate->changeBodies(stateBodies);
			stateManager.addSubState(meta_state, meta_state_deactivate);

			// create states for each body
			int bodyCount = stateBodies.size();
			std::vector<std::shared_ptr<dab::physics::State>> bodyStates(bodyCount);
			std::vector<std::shared_ptr<dab::physics::State>> deactivateStates(bodyCount);

			for (int bI = 0; bI < bodyCount; ++bI)
			{
				bodyStates[bI] = stateManager.copyState("Fluidity");
				bodyStates[bI]->changeBodies({ stateBodies[bI] }, true);

				deactivateStates[bI] = stateManager.copyState("Deactivate");
				std::vector<std::string> deactivateBodyNames;
				for (int bI2 = 0; bI2 < bodyCount; ++bI2)
				{
					if (bI2 != bI) deactivateBodyNames.push_back(stateBodies[bI2]);
				}
				deactivateStates[bI]->changeBodies(deactivateBodyNames);
				deactivateStates[bI]->changeTargets({ "fluidity" });

				stateManager.addSubState(bodyStates[bI], deactivateStates[bI]);
				stateManager.addSubState(meta_state, bodyStates[bI]);
			}

			// create state transitions
			dab::physics::StateTransitionTimed stateTransition(10.0);

			for (int bI = 0; bI < bodyCount; ++bI)
			{
				std::shared_ptr<dab::physics::State> startState = bodyStates[bI];
				std::vector<std::shared_ptr<dab::physics::State>> targetStates;

				for (int bI2 = 0; bI2 < bodyCount; ++bI2)
				{
					if (bI2 != bI) targetStates.push_back(bodyStates[bI2]);
				}

				stateManager.createStateTransition(startState, targetStates, stateTransition);
			}

			// set initially active state
			bodyStates[0]->setActive(true);
			for (int bI = 1; bI < bodyCount; ++bI) bodyStates[bI]->setActive(false);
			//meta_state->apply();

			//mStateMachine->addState(meta_state);

			travelingFluidityState = meta_state;
		}

		// create different quality traveling from body to body state
		{
			// create meta state
			std::shared_ptr<dab::physics::State> meta_state = stateManager.createState("TravelingQualities");
			std::shared_ptr<dab::physics::State> meta_state_physics = stateManager.copyState("Fluidity_Physics");
			std::shared_ptr<dab::physics::State> meta_state_deactivate = stateManager.copyState("Deactivate");

			//meta_state_physics->changeBodies(stateBodies);
			//stateManager.addSubState(meta_state, meta_state_physics);

			meta_state_deactivate->changeTargets(stateQualityBehaviors);
			meta_state_deactivate->changeBodies(stateBodies);
			stateManager.addSubState(meta_state, meta_state_deactivate);

			// create states for each quality
			std::vector<std::string> qualityStateNames = { "Fluidity", "Levitation", "Particles", "Staccato", "Thrusting" };
			std::vector<std::string> qualityBehaviorNames = { "fluidity", "levitation", "particles", "staccato", "thrusting" };
			int qualityCount = qualityStateNames.size();

			// create states for each body and each quality
			int bodyCount = stateBodies.size();
			std::vector< std::vector< std::shared_ptr<dab::physics::State> > > bodyQualityStates;

			for (int bI = 0; bI < bodyCount; ++bI)
			{
				std::vector<std::shared_ptr<dab::physics::State>> qualityStates;

				for (int qI = 0; qI < qualityCount; ++qI)
				{
					std::shared_ptr<dab::physics::State> qualityState = stateManager.copyState(qualityStateNames[qI]);
					qualityState->changeBodies({ stateBodies[bI] }, true);

					std::shared_ptr<dab::physics::State> otherBodiesDeactivateState = stateManager.copyState("Deactivate");
					std::shared_ptr<dab::physics::State> selfBodyDeactivateState = stateManager.copyState("Deactivate");

					std::vector<std::string> deactivateOtherBodyNames;

					for (int bI2 = 0; bI2 < bodyCount; ++bI2)
					{
						if (bI2 != bI) deactivateOtherBodyNames.push_back(stateBodies[bI2]);
					}

					std::vector<std::string> deactivateSelfBehaviorNames;

					for (int qI2 = 0; qI2 < qualityCount; ++qI2)
					{
						if (qI2 != qI) deactivateSelfBehaviorNames.push_back(qualityBehaviorNames[qI2]);
					}

					otherBodiesDeactivateState->changeBodies(deactivateOtherBodyNames);
					otherBodiesDeactivateState->changeTargets(qualityBehaviorNames);

					selfBodyDeactivateState->changeBodies({ stateBodies[bI] });
					selfBodyDeactivateState->changeTargets(deactivateSelfBehaviorNames);

					stateManager.addSubState(qualityState, otherBodiesDeactivateState);
					stateManager.addSubState(qualityState, selfBodyDeactivateState);

					stateManager.addSubState(meta_state, qualityState);

					qualityStates.push_back(qualityState);
				}

				bodyQualityStates.push_back(qualityStates);
			}

			// create state transitions
			dab::physics::StateTransitionTimed stateTransition(10.0);

			for (int bI = 0; bI < bodyCount; ++bI)
			{
				for (int qI = 0; qI < qualityCount; ++qI)
				{
					std::shared_ptr<dab::physics::State> startState = bodyQualityStates[bI][qI];
					std::vector<std::shared_ptr<dab::physics::State>> targetStates;

					for (int bI2 = 0; bI2 < bodyCount; ++bI2)
					{
						if (bI2 != bI)
						{
							for (int qI2 = 0; qI2 < qualityCount; ++qI2)
							{
								std::shared_ptr<dab::physics::State> targetState = bodyQualityStates[bI2][qI2];
								targetStates.push_back(targetState);
							}
						}
					}

					stateManager.createStateTransition(startState, targetStates, stateTransition);
				}
			}

			// set initial state
			for (int bI = 0; bI < bodyCount; ++bI)
			{
				for (int qI = 0; qI < qualityCount; ++qI)
				{
					bodyQualityStates[bI][qI]->setActive(false);
				}
			}
			bodyQualityStates[0][0]->setActive(true);

			travelingQualityState = meta_state;
		}

		//// transition between meta states
		dab::physics::StateTransitionTimed metaStateTransition(20.0);
		stateManager.createStateTransition(groupQualityState, { travelingFluidityState, travelingQualityState }, metaStateTransition);
		stateManager.createStateTransition(travelingFluidityState, { groupQualityState, travelingQualityState }, metaStateTransition);
		stateManager.createStateTransition(travelingQualityState, { groupQualityState, travelingFluidityState }, metaStateTransition);

		mStateMachine->addState(groupQualityState);
		mStateMachine->addState(travelingFluidityState);
		mStateMachine->addState(travelingQualityState);

		travelingFluidityState->setActive(false);
		groupQualityState->setActive(false);
		travelingQualityState->setActive(true);
		travelingQualityState->apply();
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void
ofApp::setupGraphics()
{
	//std::cout << "ofApp::setupGraphics() begin\n";

	dab::physics::Simulation& physics = dab::physics::Simulation::get();
	dab::vis::BodyVisualization& visuals = dab::vis::BodyVisualization::get();
	//visuals.camera()->setProjection(glm::vec4(20.0, 1.0, 0.1, 200.0));
	//visuals.camera()->setPosition(glm::vec3(0.0, -1.5, -2.0));
	//visuals.camera()->setRotation(glm::vec3(-90.0, 0.0, 90.0));
	visuals.camera()->setProjection(glm::vec4(20.0, 1.0, 0.1, 200.0));
	visuals.camera()->setPosition(glm::vec3(0.0, 0.0, -7.0));
	visuals.camera()->setRotation(glm::vec3(-45.0, 0.0, 45.0));

	try
	{
		visuals.loadShader("shaders/vis_shape_shader.vert", "shaders/vis_shape_shader.frag");

		// graphics
		//loadShader(mShader, "shaders/vis_shape_shader.vert", "shaders/vis_shape_shader.frag");

		ofBackground(0, 0, 0);
		ofSetFrameRate(60);
		ofSetVerticalSync(true);

		// create body shapes

		//// visual ground body shape and object
		//std::shared_ptr<dab::vis::BodyShape> visGroundShape = visuals.addBodyShape("GroundShape");
		//std::shared_ptr<dab::vis::Body> visGroundBody = visuals.addBody("ground");
		//std::shared_ptr<dab::vis::BodyPart> visGroundPart = visuals.addBodyPart("ground", "ground", "GroundShape");


		// copy bodies
		int bodyCount = physics.bodies().size();
		for (int bI = 1; bI < bodyCount; ++bI)
		{
			std::string bodyName = "onshape" + std::to_string(bI + 1);
			visuals.copyBody("onshape", bodyName);
		}

		/*
		visuals.copyBody("onshape", "onshape3");
		visuals.copyBody("onshape", "onshape4");
		visuals.copyBody("onshape", "onshape5");
		visuals.copyBody("onshape", "onshape6");
		visuals.copyBody("onshape", "onshape7");
		visuals.copyBody("onshape", "onshape8");
		*/

		//visGroundShape->material().setTransparency(0.5);
		//visGroundShape->material().setAmbientScale(0.2);
		//visGroundShape->material().setDiffuseScale(0.5);
		//visGroundShape->material().setSpecularScale(1.0);
		//visGroundShape->material().setSpecularPow(4.0);
		//visGroundShape->material().setAmbientColor(glm::vec3(0.5, 0.5, 0.5));
		//visGroundShape->material().setDiffuseColor(glm::vec3(1.0, 1.0, 1.0));

		// create bboxes of all shapes that consist of a mesh
		const std::vector<std::shared_ptr<dab::vis::BodyShape>>& visShapes = visuals.shapes();
		int visShapeCount = visShapes.size();
		for (int sI = 0; sI < visShapeCount; ++sI)
		{
			visuals.addBBox(visShapes[sI]->name());
		}

		// debug: create visual target
		//visuals.addTargetPositions(8);
		visuals.addTargetPositions(1);
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}

	//std::cout << "ofApp::setupGraphics() end\n";
}

void
ofApp::setupOsc()
{
	try
	{
		dab::com::OscControl& oscControl = dab::com::OscControl::get();

		oscControl.createReceiver("OscControlReceiver", 9003);
		oscControl.createPhysicsControl("OscControlReceiver");
		oscControl.createVisualsControl("OscControlReceiver");

		oscControl.createSender("OscPhysicsSender", "127.0.0.1", 9005);
		//oscControl.createSender("OscPhysicsSender2", "127.0.0.1", 9104); // to Pablo
	}
	catch (dab::Exception& e)
	{
		std::cout << e << "\n";
	}
}

void
ofApp::resetPhysics()
{}

//--------------------------------------------------------------
void
ofApp::update()
{
	updateOsc();
	//updatePhysics();
	updateGraphics();
}

void
ofApp::updateOsc()
{
	// receive osc control data
	dab::com::OscControl::get().update();

	// send osc data
	dab::physics::Simulation& physics = dab::physics::Simulation::get();
	dab::com::OscControl& oscControl = dab::com::OscControl::get();
	std::shared_ptr<dab::OscSender> _sender = oscControl.sender("OscPhysicsSender");
	//std::shared_ptr<dab::OscSender> _sender2 = oscControl.sender("OscPhysicsSender2");
	const std::vector<std::shared_ptr<dab::physics::Body>>& physicsBodies = physics.bodies();

	// send joint positions
	for (auto physicsBody : physicsBodies)
	{
		std::shared_ptr<dab::OscMessage> jointPositionMessage(new dab::OscMessage("/physics/joint/pos"));

		const std::string& bodyName = physicsBody->name();

		jointPositionMessage->add(bodyName);

		const std::vector<std::shared_ptr<dab::physics::BodyJoint>>& physicsJoints = physicsBody->joints();

		for (auto physicsJoint : physicsJoints)
		{
			btTransform jointTransform = physicsJoint->transform();
			const btVector3& jointPos = jointTransform.getOrigin();

			jointPositionMessage->add(jointPos[0]);
			jointPositionMessage->add(jointPos[1]);
			jointPositionMessage->add(jointPos[2]);
		}

		_sender->send(jointPositionMessage);
		//_sender2->send(jointPositionMessage);
	}

	// send joint world angles
	for (auto physicsBody : physicsBodies)
	{
		std::shared_ptr<dab::OscMessage> jointRotationMessage(new dab::OscMessage("/physics/joint/rot"));

		const std::string& bodyName = physicsBody->name();

		jointRotationMessage->add(bodyName);

		const std::vector<std::shared_ptr<dab::physics::BodyJoint>>& physicsJoints = physicsBody->joints();

		for (auto physicsJoint : physicsJoints)
		{
			btTransform jointTransform = physicsJoint->transform();
			const btQuaternion& jointRot = jointTransform.getRotation();

			jointRotationMessage->add(jointRot[0]);
			jointRotationMessage->add(jointRot[1]);
			jointRotationMessage->add(jointRot[2]);
			jointRotationMessage->add(jointRot[3]);

			//std::cout << "jrot " << jointRot[0] << " " << jointRot[1] << " " << jointRot[2] << " " << jointRot[3] << "\n";
		}

		_sender->send(jointRotationMessage);
		//_sender2->send(jointRotationMessage);
	}

	// send joint rel angles
	for (auto physicsBody : physicsBodies)
	{
		std::shared_ptr<dab::OscMessage> jointRotationMessage(new dab::OscMessage("/physics/joint/relrot"));

		const std::string& bodyName = physicsBody->name();

		jointRotationMessage->add(bodyName);

		const std::vector<std::shared_ptr<dab::physics::BodyJoint>>& physicsJoints = physicsBody->joints();

		for (auto physicsJoint : physicsJoints)
		{
			std::shared_ptr<dab::physics::UniversalJoint> ujoint = std::dynamic_pointer_cast<dab::physics::UniversalJoint>(physicsJoint);

			if (ujoint == nullptr) continue;

			const std::array<float, 3>& jointAngles = ujoint->angles();

			//std::cout << "joint " << ujoint->name() << " angles " << jointAngles[0] << " " << jointAngles[1] << " " << jointAngles[2] << "\n";


			jointRotationMessage->add(jointAngles[0]);
			jointRotationMessage->add(jointAngles[1]);
			jointRotationMessage->add(jointAngles[2]);
		}

		_sender->send(jointRotationMessage);
		//_sender2->send(jointRotationMessage);
	}
}

void
ofApp::updatePhysics()
{
	//mBehavior->update();
	dab::physics::Simulation::get().update();

	//// debug begin
	//std::shared_ptr<dab::physics::BodyPart> _bodyPart = dab::physics::Simulation::get().part("link_v2_2");
	//glm::vec3 partPos = _bodyPart->position();
	//glm::quat partRot = _bodyPart->rotation();
	//glm::vec3 partLinVel = _bodyPart->linearVelocity();
	//glm::vec3 partAngVel = _bodyPart->angularVelocity();

	//std::cout << "p " << partPos[0] << " " << partPos[1] << " " << partPos[2] << " r " << partRot[0] << " " << partRot[1] << " " << partRot[2] << " " << partRot[3] << " lv " << partLinVel[0] << " " << partLinVel[1] << " " << partLinVel[2] << " av " << partAngVel[0] << " " << partAngVel[1] << " " << partAngVel[2] << "\n";
	//// debug done
}

void
ofApp::updateGraphics()
{
	dab::vis::BodyVisualization::get().update();

	// debug : vis target position
	try
	{
		std::array<float, 3> targetPos;
		//dab::physics::Simulation::get().body("onshape")->behavior("targetpos_tip")->get("targetPos", targetPos);
		dab::physics::Simulation::get().body("onshape")->behavior("targetpos_all")->get("targetPos", targetPos);

		dab::vis::BodyVisualization::get().setTargetPosition(0, glm::vec3(targetPos[0], targetPos[1], targetPos[2]));
	}
	catch (dab::Exception& e)
	{
		std::cout << "ofApp::updateGraphics failed: " << e << "\n";
	}
}

//--------------------------------------------------------------
void ofApp::draw()
{
	glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glEnable(GL_DEPTH_TEST);

	dab::vis::BodyVisualization::get().draw();

	/*
	mGui.begin();

	dab::physics::Simulation& physics = dab::physics::Simulation::get();
	dab::vis::BodyVisualization& visuals = dab::vis::BodyVisualization::get();

	glm::vec4 camProj = visuals.camera()->projection();
	std::array<float, 4> _camProj = { camProj[0], camProj[1], camProj[2], camProj[3] };
	if (ImGui::InputFloat4("cam proj", _camProj.data()))
	{
		camProj = glm::vec4(_camProj[0], _camProj[1], _camProj[2], _camProj[3]);
		visuals.camera()->setProjection(camProj);
	}

	glm::vec3 camPos = visuals.camera()->position();
	std::array<float, 3> _camPos = {camPos.x, camPos.y, camPos.z};
	if (ImGui::InputFloat3("cam pos", _camPos.data()))
	{
		camPos = glm::vec3(_camPos[0], _camPos[1], _camPos[2]);
		visuals.camera()->setPosition(camPos);
	}

	glm::vec3 camRot = visuals.camera()->rotation();
	std::array<float, 3> _camRot = { camRot.x, camRot.y, camRot.z };
	if (ImGui::InputFloat3("cam rot", _camRot.data()))
	{
		camRot = glm::vec3(_camRot[0], _camRot[1], _camRot[2]);
		visuals.camera()->setRotation(camRot);
	}

	//// hinge motor
	//std::shared_ptr<dab::physics::HingeMotor> hingeMotor = std::static_pointer_cast<dab::physics::HingeMotor>(physics.motor("Hinge"));
	//float motorPosition = hingeMotor->position();

	//if (ImGui::InputFloat("motor pos", &motorPosition))
	//{
	//	hingeMotor->setPosition(motorPosition);
	//}

	mGui.end();
	*/
}

//--------------------------------------------------------------
void ofApp::keyPressed(int key)
{
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

bool
ofApp::loadShader(ofShader& pShader, const std::string& pVertexShader, const std::string& pFragShader)
{
	bool success;

	success = pShader.setupShaderFromFile(GL_VERTEX_SHADER, pVertexShader);
	if (success == false) std::cout << "shader " << pVertexShader << " failed: " << shaderErrorMessage(pShader, GL_VERTEX_SHADER) << "\n";

	success = pShader.setupShaderFromFile(GL_FRAGMENT_SHADER, pFragShader);
	if (success == false) std::cout << "shader " << pFragShader << " failed: " << shaderErrorMessage(pShader, GL_FRAGMENT_SHADER) << "\n";

	success = pShader.linkProgram();
	//std::cout << "link shader " << success << "\n";

	return success;
}

std::string
ofApp::shaderErrorMessage(ofShader& pShader, GLenum pShaderType)
{
	GLsizei logLength;
	GLchar  errorLog[1024];
	glGetShaderInfoLog(pShader.getShader(pShaderType), sizeof(errorLog), &logLength, errorLog);

	std::cout << "Shader info log: " << endl << errorLog << endl;

	std::string errorString = errorLog;

	return errorString;
}