
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = b'\xa7\xc6\x86P\xcf\xca\x1e\xea6k\xd0L#o\xb6\xa3'
    
_lr_action_items = {'NUMBER':([0,3,4,5,],[1,1,1,1,]),'MULOP':([1,2,6,7,8,9,],[-4,5,5,5,-2,-3,]),'$end':([1,2,7,8,9,],[-4,0,-1,-2,-3,]),'RPAREN':([1,6,7,8,9,],[-4,9,-1,-2,-3,]),'ADDOP':([1,2,6,7,8,9,],[-4,4,4,-1,-2,-3,]),'LPAREN':([0,3,4,5,],[3,3,3,3,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'expression':([0,3,4,5,],[2,6,7,8,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> expression","S'",1,None,None,None),
  ('expression -> expression ADDOP expression','expression',3,'p_expression_binop','myparser.py',19),
  ('expression -> expression MULOP expression','expression',3,'p_expression_binop','myparser.py',20),
  ('expression -> LPAREN expression RPAREN','expression',3,'p_expression_group','myparser.py',26),
  ('expression -> NUMBER','expression',1,'p_expression_number','myparser.py',31),
]