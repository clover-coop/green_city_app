class UserClass {
  String id = '', email = '', first_name = '', last_name = '', status = '', username = '',
    session_id = '', roles = '', created_at = '';
  //List<String> roles;
  List<double> lngLat = [];
  UserClass(this.id, this.email, this.first_name, this.last_name, this.status, this.username, this.session_id, this.roles,
    this.created_at, this.lngLat);
  UserClass.fromJson(Map<String, dynamic> jsonData) {
    this.id = jsonData.containsKey('_id') ? jsonData['_id'] : jsonData.containsKey('id') ? jsonData['id'] : ''; // checking '_id' & 'id' due to db user has '_id' & local storage currentUser has 'id'
    this.email = jsonData.containsKey('email') ? jsonData['email'] : '';
    this.first_name = jsonData.containsKey('first_name') ? jsonData['first_name'] : '';
    this.last_name = jsonData.containsKey('last_name') ? jsonData['last_name'] : '';
    this.status = jsonData.containsKey('status') ? jsonData['status'] : '';
    this.username = jsonData.containsKey('username') ? jsonData['username'] : '';
    this.session_id = jsonData.containsKey('session_id') ? jsonData['session_id'] : '';
    this.roles = jsonData.containsKey('roles') ? jsonData['roles'] : '';
    this.created_at = jsonData.containsKey('created_at') ? jsonData['created_at'] : '';
    this.lngLat = jsonData.containsKey('lngLat') ? [ jsonData['lngLat'][0].toDouble(), jsonData['lngLat'][1].toDouble() ] : [];
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'first_name': first_name,
    'last_name': last_name,
    'status': status,
    'username': username,
    'session_id': session_id,
    'roles': roles,
    'created_at': created_at,
    'lngLat': lngLat,
  };

  @override
  String toString() {
    return 'UserClass{id: $id, email: $email, first_name: $first_name, last_name: $last_name, status: $status, username: $username, session_id: $session_id, roles: $roles, created_at: $created_at, lngLat: $lngLat}';
  }
}
