var request;

function plan_init() {
  $('#user_email').html('Loading...');
  request = new XMLHttpRequest();
  request.open('GET', '/fetchplan', true);
  request.onreadystatechange = plan_receive;
  request.send(null);
}

function plan_receive() {
  console.log('plan_receive %d %d', request.readyState, request.status);
  if (request.readyState == 4) {
    if (request.status == 200) {
      plan_load(request.responseXML);
    }
  }
}

var MAX_FAMILY_MEMBERS = 20;

function plan_load(xmlDoc) {
  console.log('plan_load');
  var xmlPlan = xmlDoc.getElementsByTagName('plan')[0];
  var plan = xmlNodeToJson(xmlPlan);
  console.log(plan);
  $('#user_name').html(plan.user_name.$t);
  $('#user_email').html(plan.user_email.$t);
  $('#out_of_town_contact').val(plan.out_of_town_contact.$t);
  $('#neighborhood_meeting_place').val(plan.neighborhood_meeting_place.$t);
  $('#regional_meeting_place').val(plan.regional_meeting_place.$t);
  $('evacuation_location').val(plan.evacuation_location.$t);
  var members_div = $('#family_members');
  var members_list = listify(plan.family_member);
  for (var i = 0; i != MAX_FAMILY_MEMBERS; i = i + 1) {
    var family_member = members_list[i];
    var div = $('<div></div>');
    var input = $('<input>').attr('type', 'text')
        .attr('name', 'family_member' + i);
    if (family_member) {
      input.val(family_member.$t);
    }
    div.append(input);
    members_div.append(div);
  }
  return;
}
