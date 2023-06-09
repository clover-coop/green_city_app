import 'dart:convert';
import 'dart:html';
import 'package:flutter/material.dart';
import 'package:localstorage/localstorage.dart';
import 'package:location/location.dart';

import '../../common/localstorage_service.dart';
import '../../common/socket_service.dart';
import './user_class.dart';

class CurrentUserState extends ChangeNotifier {
  SocketService _socketService = SocketService();
  LocalstorageService _localstorageService = LocalstorageService();

  UserClass? _currentUser;
  bool _isLoggedIn = false;
  LocalStorage? _localstorage = null;
  List<String> _routeIds = [];
  String _status = "done";

  get isLoggedIn => _isLoggedIn;

  get currentUser => _currentUser;

  get status => _status;

  void init() {
    if (_routeIds.length == 0) {
      _routeIds.add(_socketService.onRoute('getUserSession', callback: (String resString) {
        var res = json.decode(resString);
        var data = res['data'];
        if (data['valid'] == 1 && data.containsKey('user')) {
          UserClass user = UserClass.fromJson(data['user']);
          if (user.id.length > 0) {
            setCurrentUser(user);
          }
        }
        _status = "done";
      }));

      _routeIds.add(_socketService.onRoute('logout', callback: (String resString) {
        _status = "done";
      }));
    }
  }

  void getLocalstorage() {
    if (_localstorage == null) {
      init();
      _localstorage = _localstorageService.localstorage;
    }
  }

  void setCurrentUser(UserClass user) {
    _currentUser = user;
    _isLoggedIn = true;
    _socketService.setAuth(user.id, user.session_id);

    getLocalstorage();
    _localstorage?.setItem('currentUser', user.toJson());

    notifyListeners();
  }

  void clearUser() {
    _currentUser = null;
    _isLoggedIn = false;
    _socketService.setAuth('', '');

    getLocalstorage();
    _localstorage?.deleteItem('currentUser');

    notifyListeners();
  }

  void checkAndLogin() {
    getLocalstorage();
    Map<String, dynamic>? _localStorageUser = _localstorage?.getItem('currentUser');
    UserClass? user = _localStorageUser != null? UserClass.fromJson(_localStorageUser):null;
    if (user != null) {
      _status = "loading";
      _socketService.emit('getUserSession', {  'user_id': user.id, 'session_id': user.session_id });
      _currentUser = user;
      _isLoggedIn = true;
    }
  }

  void logout() {
    if (_currentUser != null) {
      _status = "loading";
      _socketService.emit('logout', { 'user_id': _currentUser!.id, 'session_id': _currentUser!.session_id });
    }
  }

  Future<List<dynamic>> getUserLocation() async {
    List<dynamic> _lngLat = [];
    LocalStorage _localStorage = _localstorageService.localstorage;
    List<dynamic>? _lngLatLocalStored = _localStorage.getItem('lngLat');
    if (_lngLatLocalStored != null){
      _lngLat = _lngLatLocalStored;
    }
    else if (_currentUser != null && _currentUser?.lngLat != []){
      _lngLat = _currentUser!.lngLat;
    } else {
      LocationData coordinates = await Location().getLocation();
      if (coordinates.latitude != null) {
        _localstorageService.localstorage.setItem('lngLat', [coordinates.longitude, coordinates.latitude]);
          _lngLat = [coordinates.longitude!, coordinates.latitude!];
      }
    }
    return _lngLat;
  }

  bool hasRole(String role) {
    if (_currentUser != null) {
      List<String> roles = _currentUser!.roles.split(",");
      if (roles.contains(role)) {
        return true;
      }
    }
    return false;
  }

  @override
  String toString() {
    return 'CurrentUserState{_currentUser: $_currentUser, _isLoggedIn: $_isLoggedIn, _routeIds: $_routeIds, _status: $_status}';
  }
}